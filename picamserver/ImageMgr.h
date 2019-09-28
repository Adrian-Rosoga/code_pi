#pragma once

#include <vector>
#include <mutex>
#include <condition_variable>
#include <thread>

struct Image
{
    explicit Image(int maxImageSize)
    {
        image_.reset(new char[maxImageSize]);
        size = 0;
        inUse = false;
    }
    char* getBuffer() { return image_.get(); }
    const char* getBuffer() const { return image_.get(); }
    int size;
    bool inUse;
    
private:
    std::unique_ptr<char[]> image_;
};

class ImageMgr
{
public:
    ImageMgr(int maxImageSize, const std::string& photoCmd);
    ~ImageMgr();
    
    void startPhotoThread();
    const Image& getImage();
    void doneImage();
    
private:
    std::vector<Image> images_;
    std::mutex mtx_[2];
    std::condition_variable cv_[2];
    int nbReaders[2];
    int writeIx_, readIx_, readSlot_;
    const int maxImageSize_;
    std::thread takePhotoThread_;
    void takePhotoThreadLoop_();
    const std::string photoCmd_;
};
