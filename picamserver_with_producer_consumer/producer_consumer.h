#pragma once

/*
 * Producer-Consumer(s) with a twist
 */

#include <functional>

void produce(std::function<void(int index_to_use)>& callback);
void consume(std::function<void(int index_to_use)>& callback);
void consume_no_contention(std::function<void(int index_to_use)>& callback);