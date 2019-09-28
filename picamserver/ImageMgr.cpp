#include "ImageMgr.h"
#include "util.h"

#include <unistd.h>
#include <iostream>
#include <chrono>
#include <cassert>

int exec(const char* cmd, char* buffer, unsigned int bufferSize)
{
    std::shared_ptr<FILE> pipePtr(popen(cmd, "r"), pclose);
    
    if (!pipePtr) { return -1; }
    
    char* pos = buffer;
    while (!feof(pipePtr.get()) && bufferSize - (pos - buffer) > 0)
    {
        size_t readCount;
        readCount = fread(pos, 1, bufferSize - (pos - buffer), pipePtr.get());
        pos += readCount;
    }
    
    return pos - buffer;
}

void execTest()
{
    const int BUFFER_SIZE = 10000000;
    std::unique_ptr<char[]> buffer{new char[BUFFER_SIZE]};
    
    int outputSize = exec("/bin/ls -lart", buffer.get(), BUFFER_SIZE - 1);
    
    if (outputSize == -1)
    {
        std::cout << "exec: Error running the command" << std::endl;
        return;
    }
    
    buffer[outputSize] = '\0';
    
    std::cout << "exec: " << outputSize << " bytes:" << std::endl;
    std::cout << buffer.get() << std::endl;
}

std::string get_temperature()
{
    const int temperatureBufferSize = 100;
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

std::string led_off()
{
    const int bufferSize = 100;
    char buffer[bufferSize];
    const int nbBytes = exec("sudo /home/pi/code_pi/picamserver/LED.py", buffer, bufferSize - 1);
    if (nbBytes == -1)
    {
        std::cerr << "Couldn't turn the LED off" << std::endl;
        exit(1);
    }
    buffer[nbBytes] = '\0';
    std::cout << "Turn LED off msg: " << buffer << std::endl;
    return buffer;
}

ImageMgr::ImageMgr(int maxImageSize, const std::string& photoCmd) : maxImageSize_(maxImageSize), photoCmd_(photoCmd)
{
    images_.emplace_back(maxImageSize);
    images_.emplace_back(maxImageSize);
    writeIx_ = 0;
    readIx_ = 1;
    nbReaders[0] = nbReaders[1] = 0;
}

void ImageMgr::startPhotoThread()
{
    takePhotoThread_ = std::thread(&ImageMgr::takePhotoThreadLoop_, this);
}

ImageMgr::~ImageMgr()
{
    takePhotoThread_.join();
}

const Image& ImageMgr::getImage()
{
    readSlot_ = readIx_;
    ++nbReaders[readSlot_];
    //std::cout << std::this_thread::get_id() << " taken readSlot_ = " << readSlot_ << ", ++nbReaders[readSlot_] = " <<  nbReaders[readSlot_] << std::endl;
    log(std::this_thread::get_id(), " taken readSlot_ = ", readSlot_, ", ++nbReaders[readSlot_] = ", nbReaders[readSlot_]);
    return images_[readSlot_];
}

void ImageMgr::doneImage()
{
    --nbReaders[readSlot_];
    //std::cout << std::this_thread::get_id() << " released readSlot_ = " << readSlot_ << ", ++nbReaders[readSlot_] = " <<  nbReaders[readSlot_] << std::endl;
    log(std::this_thread::get_id(), " released readSlot_ = ", readSlot_, ", ++nbReaders[readSlot_] = ", nbReaders[readSlot_]);
	assert(nbReaders[readSlot_] >= 0);
}

void ImageMgr::takePhotoThreadLoop_()
{
    while (1)
    {
        int nbBytes;
        
        {
            int sleepCount = 0;
            while (nbReaders[writeIx_] > 0)
            {
                usleep(100000); // 100 msecs
                ++sleepCount;
                
            }
            
            if (sleepCount > 0)
            {
                std::cout << "---------- Slept = " << sleepCount << std::endl;
            }
            
            //std::cout << get_temperature() << std::endl;

#if TEST        
            if (writeIx_ == 0)
            {
                nbBytes = exec("cat z.jpg", images_[writeIx_].getBuffer(), maxImageSize_);            
                std::cout << "z.jpg, size = " << nbBytes << ", writeIx_ = " << writeIx_ << std::endl;
            }
            else
            {
                nbBytes = exec("cat z1.jpg", images_[writeIx_].getBuffer(), maxImageSize_);
                std::cout << "z1.jpg, size = " << nbBytes << ", writeIx_ = " << writeIx_ << std::endl;
            }
#else
            //led_off(); // Doesn't help anyway
            
            nbBytes = exec(photoCmd_.c_str(), images_[writeIx_].getBuffer(), maxImageSize_);
            //std::cout << std::this_thread::get_id() << " Photo thread - size = " << nbBytes << ", writeIx_ = " << writeIx_ << std::endl;
            log(std::this_thread::get_id(), " Photo thread - size = ", nbBytes, ", writeIx_ = ", writeIx_);
#endif
            
            if (nbBytes == -1)
            {
                std::cerr << "Taking image failed" << std::endl;
                exit(1);
            }
            
            images_[writeIx_].size = nbBytes;
            
            readIx_ = writeIx_;
    
            writeIx_ = (writeIx_ + 1) % 2;
    
#if TEST
            // ADIRX - Fake timer used during testing
            // std::this_thread::sleep_for(std::chrono::seconds(6)); // sleep_for() not supported in gcc 4.6.3 but ok in 4.9.2
            sleep(6);
#else     
#endif
        }
    }
}
