#pragma once

#include <iostream>
#include <chrono>
#include <ctime>

template<typename Clock, typename Duration>
std::ostream &operator<<(std::ostream &stream,
  const std::chrono::time_point<Clock, Duration> &time_point) {
  const time_t time = Clock::to_time_t(time_point);
#if __GNUC__ > 4 || \
    ((__GNUC__ == 4) && __GNUC_MINOR__ > 8 && __GNUC_REVISION__ > 1)
  // Maybe the put_time will be implemented later?
  struct tm tm;
  localtime_r(&time, &tm);
  return stream << std::put_time(&tm, "c");
#else
  char buffer[26];
  ctime_r(&time, buffer);
  buffer[24] = '\0';  // Removes the newline that is added
  return stream << buffer;
#endif
}

template <typename T>
void logV(const T& t)
{
    std::cout << t << std::endl;
}

template <typename T, typename... Rest>
void logV(const T& t, const Rest&... rest)
{
    std::cout << t;
    logV(rest...);
}

template <typename T, typename... Rest>
void log(const T& t, const Rest&... rest)
{
    std::cout << std::chrono::system_clock::now() << " - ";
    std::cout << t;
    logV(rest...);
}