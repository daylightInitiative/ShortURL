# ShortURL
A url shortening microservice API implemented with flask

[0.1.1] Improvements: Switching from database to Redis (redis[hiredis]) for caching, rate limiting and speed
[0.1.2] Added run file for linux, seperated css into a seperate file

## How to run
On windows install ubuntu WSL (or any other distro) and run ```redis-server``` Then run .\run.ps1 while in the main directory.
On linux simply install redis-server and then run ```./run.sh``` while in the main directory.
The website should be hosted on https://localhost:5000/
