#include <sys/socket.h>
#include <sys/types.h>
#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/stat.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <string.h>
#include <unistd.h>
#include <iostream>
#include <sstream>
#include <fstream>
#include <memory>
#include <algorithm>
#include <functional>
#include <future>

#include "ImageMgr.h"
#include "producer_consumer.h"
#include "util.h"
#include "ThreadPool.h"

#define ASSERTNOERR(x, msg) do { if ((x) == -1)\
{ std::cout << "\nAssert failed!\n"; perror(msg); exit(-1); } } while (0)

#define CHECK_WRITE_SOCKET(n) do { if ((n) < 0)\
{ std::cerr << "Error: Writing to socket: Line " << __LINE__ << std::endl; } } while (0)

//const std::string RaspistillCmd = "raspistill -n -q 100 -w 1440 -h 1080 -o -";
const std::string RaspistillCmd = "raspistill -n -q 100 -w 720 -h 540 -o -";
const int LISTEN_BACKLOG = 128; // i.e. /proc/sys/net/core/somaxconn

const std::string HTTP_PAGE_MAIN =
R"foo(HTTP/1.0 200 OK
Server: picamserver
Content-type: text/html

<!DOCTYPE html>
<HTML>
    <HEAD>
        <TITLE>PiCamera</TITLE>
        <META HTTP-EQUIV=PRAGMA CONTENT=NO-CACHE>
        <META HTTP-EQUIV=EXPIRES CONTENT=-1>
        <META HTTP-EQUIV=REFRESH CONTENT=10>
    </HEAD>
    <BODY BGCOLOR="BLACK">
        <H2 ALIGN="CENTER">
        <B><FONT COLOR="YELLOW">Pi Cam</FONT></B>
        </H2>
        <P ALIGN="CENTER">
        <IMG SRC="picamimage" STYLE="HEIGHT: 100%" ALT="NO IMAGE!" WIDTH="720" HEIGHT="540">
        </P>
    </BODY>
</HTML>
)foo";

const std::string HTTP_HEADER_200_OK =
R"foo(HTTP/1.1 200 OK
Server: picamserver
Accept-Ranges: bytes
)foo";

const std::string HTTP_HEADER_404_NOT_FOUND =
R"foo(HTTP/1.1 404 Not Found
Server: picamserver)foo";

const std::string HTTP_BODY_404_NOT_FOUND =
R"foo(<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">
<html><head>
<title>404 Not Found</title>
</head><body>
<h1>Not Found</h1>
<p>The requested URL was not found.</p>
</body></html>
)foo";

std::string get_temperature()
{
    const int temperatureBufferSize = 32;
    char temperatureBuffer[temperatureBufferSize];
    const int nbBytes = exec("sudo /home/pi/code_pi/HTU21/HTU21D.py", temperatureBuffer, temperatureBufferSize - 1);
    if (nbBytes == -1)
    {
        std::cerr << "Couldn't get the temperature" << std::endl;
        exit(1);
    }
    temperatureBuffer[nbBytes] = '\0';
    return temperatureBuffer;
}

int process(int fd, std::reference_wrapper<ImageMgr> imageMgrW)
{
    ImageMgr& imageMgr = imageMgrW.get();
    
    const int MAX_REQUEST = 1024;
    char request[MAX_REQUEST];
    
    int pos = 0;
    while (1)
    {
        auto n = read(fd, request + pos, sizeof(request) - pos);
        pos += n;
        
        if (n == 0) { break; }
        if (pos == MAX_REQUEST) { break; } // Huge header, tread with care
        
        // Find the end of the headers - '\r\n\r\n' or, to be tolerant, '\n\n' as well
        if (strstr(request, "\r\n\r\n") || strstr(request, "\n\n")) { break; }
    }
    
    // Print the request line
    auto request_end = strstr(request, "\n");
    if (request_end)
    {
        std::for_each(request, request_end, [](char c) { std::cout << c; });
        std::cout << "\n";
    }
    
    int n = 0;
    if (strstr(request, "GET / HTTP"))
    {
        std::string page(HTTP_PAGE_MAIN);
        
        std::ostringstream str;
        str << "Pi Camera - " << get_temperature() << " - "
            << std::chrono::system_clock::now();
        
        auto pos = page.find("Pi Cam");
        page.replace(pos, strlen("Pi Cam"), str.str());
        
        n = write(fd, page.c_str(), page.size());
        CHECK_WRITE_SOCKET(n);
    }
    else if (strstr(request, "GET /picamimage HTTP"))
    {
        n = write(fd, HTTP_HEADER_200_OK.c_str(), HTTP_HEADER_200_OK.size());
        CHECK_WRITE_SOCKET(n);
        
        std::ostringstream str;
        
        str << "Content-Type: image/jpeg" << "\n";
        
        std::function<void(int)> callback = [&](int index) {
                    
            str << "Content-lenght: " << imageMgr[index].size << "\r\n\r\n";
            n = write(fd, str.str().c_str(), str.str().size());
            //std::cout << str.str().c_str() << std::endl;
            CHECK_WRITE_SOCKET(n);
            
            n = write(fd, imageMgr[index].getBuffer(), imageMgr[index].size);
            CHECK_WRITE_SOCKET(n);
            
            log(std::this_thread::get_id(), " consume: size=", imageMgr[index].size, " index=", index);
        };
        
        // ADIRX
        consume(callback);
        //consume_no_contention(callback);
        
    }
    else if (strstr(request, "GET /favicon.ico HTTP"))
    {
        n = write(fd, HTTP_HEADER_200_OK.c_str(), HTTP_HEADER_200_OK.size());
        CHECK_WRITE_SOCKET(n);
        
        std::ostringstream str;
        
        std::ifstream fav("favicon.ico", std::ios::binary);           
        if (!fav)
        {
            std::cerr << "Cannot open favicon.ico" << std::endl;
            str << "Content-lenght: " << 0 << "\n\n";
            // ADIRX
            return -1;
        }
        
        fav.seekg(0, std::ios::end);
        const int size = fav.tellg();
             
        str << "Content-Type: image/ico" << "\n"; 
        str << "Content-lenght: " << size << "\n\n";           
        n = write(fd, str.str().c_str(), str.str().size());
        CHECK_WRITE_SOCKET(n);
        
        fav.seekg(0, std::ios::beg);
        
        const int BUFFER_SIZE = 1024;
        char buffer[BUFFER_SIZE];
        while (fav.read(buffer, BUFFER_SIZE))
        {
            n = write(fd, buffer, fav.gcount());
            CHECK_WRITE_SOCKET(n);
        }
    }
    else
    {
        // Bail out  
        std::ostringstream str;
        str << HTTP_HEADER_404_NOT_FOUND << "\n";
        str << "Content-lenght: " << HTTP_BODY_404_NOT_FOUND.size() << "\n\n";
        str << HTTP_BODY_404_NOT_FOUND;
        
        //std::cout << str.str() << std::endl;
        
        n = write(fd, str.str().c_str(), str.str().size());
        CHECK_WRITE_SOCKET(n);
        
        std::cout << "Error: Unknown request: '" << request << "'" << std::endl;
    }
    
    close(fd);
    
    return 0;
}

int main(int argc, char** argv)
{
    if (argc != 2)
    {
        std::cerr << "Usage: " << argv[0] << " <port>" << std::endl;
        exit(1);
    }
    
    const int port = atoi(argv[1]);
    
    auto s = socket(AF_INET, SOCK_STREAM, 0);
    
    ASSERTNOERR(s, "socket");
    
    int reuse = 1;
    if (setsockopt(s, SOL_SOCKET, SO_REUSEADDR, (const char*)&reuse, sizeof(reuse)) < 0)
        perror("setsockopt(SO_REUSEADDR) failed");

    #ifdef SO_REUSEPORT
    if (setsockopt(s, SOL_SOCKET, SO_REUSEPORT, (const char*)&reuse, sizeof(reuse)) < 0) 
        perror("setsockopt(SO_REUSEPORT) failed");
    #endif
    
    struct sockaddr_in my_addr;
    
    memset(&my_addr, 0, sizeof(struct sockaddr));

    my_addr.sin_family = AF_INET;
    my_addr.sin_port = htons(port);
    my_addr.sin_addr.s_addr = INADDR_ANY;
    
    int rc = bind(s, (struct sockaddr*)&my_addr, sizeof(my_addr));
    
    ASSERTNOERR(rc, "bind");
    
    rc = listen(s, LISTEN_BACKLOG);
    
    ASSERTNOERR(rc, "listen");
    
    ImageMgr imageMgr;
    imageMgr.startImageThread(RaspistillCmd);
    
    ThreadPool pool(10);
      
    while (1)
    { 
        struct sockaddr_in peer_adr;
        socklen_t addrlen = sizeof(peer_adr);
        
        int fd = accept(s, (struct sockaddr*)&peer_adr, &addrlen);
        
        ASSERTNOERR(fd, "accept");
    
#if 0
        process(fd, std::ref(imageMgr));
#endif

#if 1
        pool.enqueue(process, fd, std::ref(imageMgr));
#endif
    }
    
    close(s);
    
    return 0;
}
