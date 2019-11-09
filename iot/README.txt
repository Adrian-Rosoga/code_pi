
pip3 install adafruit-io
pip3 install ilock

2019-11-08 14:16:05 Temp=21.5*C Humidity=51.3%
2019-11-08 14:17:08 Temp=21.5*C Humidity=51.4%
Traceback (most recent call last):
  File "/usr/lib/python3/dist-packages/urllib3/connection.py", line 159, in _new_conn
    (self._dns_host, self.port), self.timeout, **extra_kw)
  File "/usr/lib/python3/dist-packages/urllib3/util/connection.py", line 57, in create_connection
    for res in socket.getaddrinfo(host, port, family, socket.SOCK_STREAM):
  File "/usr/lib/python3.7/socket.py", line 748, in getaddrinfo
    for res in _socket.getaddrinfo(host, port, family, type, proto, flags):
socket.gaierror: [Errno -3] Temporary failure in name resolution

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/usr/lib/python3/dist-packages/urllib3/connectionpool.py", line 600, in urlopen
    chunked=chunked)
  File "/usr/lib/python3/dist-packages/urllib3/connectionpool.py", line 343, in _make_request
    self._validate_conn(conn)
  File "/usr/lib/python3/dist-packages/urllib3/connectionpool.py", line 841, in _validate_conn
    conn.connect()
  File "/usr/lib/python3/dist-packages/urllib3/connection.py", line 301, in connect
    conn = self._new_conn()
  File "/usr/lib/python3/dist-packages/urllib3/connection.py", line 168, in _new_conn
    self, "Failed to establish a new connection: %s" % e)
urllib3.exceptions.NewConnectionError: <urllib3.connection.VerifiedHTTPSConnection object at 0x7582c9f0>: Failed to establish a new connection: [Errno -3] Temporary failure in name resolution

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/usr/lib/python3/dist-packages/requests/adapters.py", line 449, in send
    timeout=timeout
  File "/usr/lib/python3/dist-packages/urllib3/connectionpool.py", line 638, in urlopen
    _stacktrace=sys.exc_info()[2])
  File "/usr/lib/python3/dist-packages/urllib3/util/retry.py", line 398, in increment
    raise MaxRetryError(_pool, url, error or ResponseError(cause))
urllib3.exceptions.MaxRetryError: HTTPSConnectionPool(host='io.adafruit.com', port=443): Max retries exceeded with url: /api/v2/arosoga/feeds/rafi-temperature/data (Caused by NewConnectionError('<urllib3.connection.VerifiedHTTPSConnection object at 0x7582c9f0>: Failed to establish a new connection: [Errno -3] Temporary failure in name resolution'))

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "./climate.py", line 51, in main
    send_readings(aio, temperature_feed, humidity_feed, last_updated_feed)
  File "./climate.py", line 27, in send_readings
    aio.send(temperature_feed.key, str(temperature))
  File "/home/pi/.local/lib/python3.7/site-packages/Adafruit_IO/client.py", line 154, in send_data
    return self.create_data(feed, payload)
  File "/home/pi/.local/lib/python3.7/site-packages/Adafruit_IO/client.py", line 254, in create_data
    return Data.from_dict(self._post(path, data._asdict()))
  File "/home/pi/.local/lib/python3.7/site-packages/Adafruit_IO/client.py", line 126, in _post
    data=json.dumps(data))
  File "/usr/lib/python3/dist-packages/requests/api.py", line 116, in post
    return request('post', url, data=data, json=json, **kwargs)
  File "/usr/lib/python3/dist-packages/requests/api.py", line 60, in request
    return session.request(method=method, url=url, **kwargs)
  File "/usr/lib/python3/dist-packages/requests/sessions.py", line 533, in request
    resp = self.send(prep, **send_kwargs)
  File "/usr/lib/python3/dist-packages/requests/sessions.py", line 646, in send
    r = adapter.send(request, **kwargs)
  File "/usr/lib/python3/dist-packages/requests/adapters.py", line 516, in send
    raise ConnectionError(e, request=request)
requests.exceptions.ConnectionError: HTTPSConnectionPool(host='io.adafruit.com', port=443): Max retries exceeded with url: /api/v2/arosoga/feeds/rafi-temperature/data (Caused by NewConnectionError('<urllib3.connection.VerifiedHTTPSConnection object at 0x7582c9f0>: Failed to establish a new connection: [Errno -3] Temporary failure in name resolution'))

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "./climate.py", line 61, in <module>
    main()
  File "./climate.py", line 52, in main
    except simplejson.errors.JSONDecodeError as ex:
NameError: name 'simplejson' is not defined
climate$ 
