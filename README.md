Сервер sync/threadpool  
Результаты нагрузочного тестирования:  
Server Software:        CustomServer/1.0  
Server Hostname:        localhost  
Server Port:            8080  

Document Path:          /  
Document Length:        438 bytes  

Concurrency Level:      100  
Time taken for tests:   122.473 seconds  
Complete requests:      50000  
Failed requests:        270  
   (Connect: 0, Receive: 90, Length: 90, Exceptions: 90)  
Total transferred:      29197350 bytes  
HTML transferred:       21860580 bytes  
Requests per second:    408.25 [#/sec] (mean)  
Time per request:       244.945 [ms] (mean)  
Time per request:       2.449 [ms] (mean, across all concurrent requests)  
Transfer rate:          232.81 [Kbytes/sec] received  

Connection Times (ms)  
              min  mean[+/-sd] median   max  
Connect:        0   16 437.0      0   64835  
Processing:     2  216 4888.1      6  115280  
Waiting:        0    9 293.1      6   55354  
Total:          3  232 5178.2      6  122470  

Percentage of the requests served within a certain time (ms)  
  50%      6  
  66%      7  
  75%      7  
  80%      7  
  90%      8  
  95%      9  
  98%     10  
  99%     12  
 100%  122470 (longest request)  
