// TODO

void test()
{
    std::function<void(int)> fct_producer = [](int index) { std::cout << "PROD index=" << index << std::endl; };
    
    std::thread producer([&fct_producer] { while (1) produce(fct_producer); });
    sleep(10);
    
    std::function<void(int)> fct_consumer = [](int index) { std::cout << "CONS index=" << index << std::endl; };
    
    std::thread consumer1([&fct_consumer] { while (1) consume(fct_consumer); });
    std::thread consumer2([&fct_consumer] { while (1) consume(fct_consumer); });
    std::thread consumer3([&fct_consumer] { while (1) consume(fct_consumer); });
    std::thread consumer4([&fct_consumer] { while (1) consume(fct_consumer); });
    
    producer.join();
    consumer1.join();
    consumer2.join();
    consumer3.join();
    consumer4.join();
}

int main(int argc, char** argv)
{
    test();
}