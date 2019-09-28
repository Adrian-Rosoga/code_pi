/*
Adrian Rosoga
16 Feb 2016
picamserver
Serves Pi camera images on HTTP
 */

#include <sys/socket.h>
#include <sys/types.h>
#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/types.h>
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

#include "ImageMgr.h"

#define ASSERTNOERR(x, msg) do { if ((x) == -1) { perror(msg); exit(-1); } } while (0)

const std::string RaspistillCmd = "raspistill -n -q 100 -w 1440 -h 1080 -o -";
const int MAX_PICTURE_SIZE = 3000000;
const int LISTEN_BACKLOG = 5;

extern std::string get_temperature();
extern std::string led_off();
        
const std::string HTML_PAGE =
R"foo(HTTP/1.0 200 OK
Server: picamserver
Content-type: text/html

<!DOCTYPE html>
<HTML>
    <HEAD>
        <TITLE>PiCamServer</TITLE>
        <META HTTP-EQUIV=PRAGMA CONTENT=NO-CACHE>
        <META HTTP-EQUIV=EXPIRES CONTENT=-1>
        <META HTTP-EQUIV=REFRESH CONTENT=10>
        <script src="http://code.jquery.com/jquery-1.8.3.min.js" type="text/javascript"></script>
        
        <SCRIPT type="text/javascript">
startTimer = function() {
  var time;
  time = 0;
  setInterval((function() {
    var hour, min, sec, str;
    time++;
    sec = time % 60;
    min = (time - sec) / 60 % 60;
    hour = (time - sec - (min * 60)) / 3600;
    count = hour + ':' + ('0' + min).slice(-2) + ':' + ('0' + sec).slice(-2);
    $('span').text(count);
  }), 1000);
};

$( document ).ready(function() {
    startTimer();
});
</SCRIPT>

    </HEAD>
    <BODY BGCOLOR="BLACK" BACKGROUND_X="grill.jpg">
        <H2 ALIGN="CENTER">
        <B><FONT COLOR="YELLOW">PiCamServer - %TEMP_HUMIDITY% - %TIME% - <span class="responseTime"></span></FONT></B>
        </H2>
        <P ALIGN="CENTER">
        <IMG SRC="picamimage" STYLE="HEIGHT: 100%" ALT="NO IMAGE!" WIDTH_X="420" HEIGHT_X="420">
        </P>
    </BODY>
</HTML>
)foo";

const std::string IMAGE_PAGE =
R"foo(HTTP/1.1 200 OK
Date: Sun, 18 Oct 2009 12:10:12 GMT
Server: picamserver
Accept-Ranges: bytes
)foo";

int main(int argc, char** argv)
{ 
    if (argc != 2)
    {
        std::cerr << "Usage: " << argv[0] << " <port>" << std::endl;
        exit(1);
    }
    
    const int port = atoi(argv[1]);
    
    int s = socket(AF_INET, SOCK_STREAM, 0);
    
    ASSERTNOERR(s, "socket");
    
    int reuse = 1;
    if (setsockopt(s, SOL_SOCKET, SO_REUSEADDR, (const char*)&reuse, sizeof(reuse)) < 0)
        perror("setsockopt(SO_REUSEADDR) failed");

    #ifdef SO_REUSEPORT
    std::cout << "SO_REUSEPORT is defined" << std::endl;
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
    
    ImageMgr imageMgr(MAX_PICTURE_SIZE, RaspistillCmd);
    imageMgr.startPhotoThread();
      
    while (1)
    {
        fd_set fds;
        
        FD_ZERO(&fds);        
        FD_SET(s, &fds);
        
        int rc = select(s + 1, &fds, nullptr, nullptr, nullptr);
        
        ASSERTNOERR(rc, "select");
        
        struct sockaddr_in peer_adr;
        socklen_t addrlen = sizeof(peer_adr);
        
        int fd = accept(s, (struct sockaddr*)&peer_adr, &addrlen);
        
        ASSERTNOERR(fd, "accept");
        
        std::string request;
        request.reserve(1024);
        
        char buf[256];
        while (1)
        {
            auto n = read(fd, buf, sizeof(buf) - 1);
            if (n == 0) { break; }
            
            bool read_all = false;
            // Find the end of the headers, i.e. \r\n\r\n
            // TODO - Make it work with \n only
            if (n >=4 && buf[n-4] == 0x0d && buf[n-3] == 0x0a && buf[n-2] == 0x0d && buf[n-1] == 0x0a)
            {
                read_all = true;
            };
            
            buf[n] = '\0';
            //std::cout << buf;
            
            // Todo - Check buffer overflow
            request += buf;
            
            if (read_all) { break; }
        }
        
        // Print the request line
        auto pos = request.find_first_of('\n');
        if (pos != std::string::npos)
        {
            //std::cout << request.substr(0, pos) << std::endl;
        }
        //std::cout << std::endl << "---END---" << std::endl;
        
        int n = 0;
        if (request.find("GET / HTTP") != std::string::npos)
        {
            //n = write(fd, HTML_PAGE.c_str(), HTML_PAGE.size());
            std::string page(HTML_PAGE);
            
            auto pos = page.find("%TEMP_HUMIDITY%");
            page.replace(pos, strlen("%TEMP_HUMIDITY%"), get_temperature());
            
            pos = page.find("%TIME%");
            page.replace(pos, strlen("%TIME%"), "TODO");
            
            n = write(fd, page.c_str(), page.size());
        }
        else if (request.find("GET /picamimage HTTP") != std::string::npos)
        {
            n = write(fd, IMAGE_PAGE.c_str(), IMAGE_PAGE.size());
            
            std::ostringstream str;
            
            str << "Content-Type: image/jpeg" << "\n";
            
            //
            // TESTING - Simulate a slow link
            //
            //sleep(2);
            
            const Image& image = imageMgr.getImage();
    
            if (image.size == -1)
            {
                std::cout << "exec: Error running the command" << std::endl;
                str << 0 << "\n\n";
                continue;
            }
            
            //std::cout << "Image size = " << image.size << std::endl;
                        
            str << "Content-lenght: " << image.size << "\n\n";
            write(fd, str.str().c_str(), str.str().size());            
            write(fd, image.getBuffer(), image.size);
            
            imageMgr.doneImage();
        }
        else if (request.find("GET /favicon.ico HTTP") != std::string::npos)
        {
            write(fd, IMAGE_PAGE.c_str(), IMAGE_PAGE.size());
            
            std::ostringstream str;
            
            std::ifstream fav("favicon.ico", std::ios::binary);           
            if (!fav)
            {
                std::cout << "Cannot open favicon.ico" << std::endl;
                str  << "Content-lenght: " << 0 << "\n\n";
                continue;
            }
            
            fav.seekg(0, std::ios::end);
            const int size = fav.tellg();
                 
            str << "Content-Type: image/ico" << "\n"; 
            str << "Content-lenght: " << size << "\n\n";           
            write(fd, str.str().c_str(), str.str().size());
            
            fav.seekg(0, std::ios::beg);
            
            // TODO - Test for exceptions when favicon.ico doesn't exist
            const int BUFFER_SIZE = 1024;
            char buffer[BUFFER_SIZE];
            while (fav.read(buffer, BUFFER_SIZE))
            {
                write(fd, buffer, fav.gcount());
            }
        }
        else
        {
            // Bail out
            // Todo - Replace with 404 not found
            write(fd, IMAGE_PAGE.c_str(), IMAGE_PAGE.size());
            std::ostringstream str;
            str << "Content-lenght: " << 0 << "\n\n";
            write(fd, str.str().c_str(), str.str().size());
            std::cout << "ERROR - Unknown request: " << request << std::endl;
        }
        
        if (n < 0)
        {
            std::cout << "ERROR - Writing to socket" << std::endl;
        }
        
        close(fd);
    }
    
    close(s);
    
    return 0;
}
