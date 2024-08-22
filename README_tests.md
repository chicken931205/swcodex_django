# app-seed test automation

## Prerequisites

- docker installed

### run on test on windows
```bash
test.bat
```

### run test on unix based os
```bash
./test.sh
```



## High Level End To End Test Diagram 
[HLD Image](./e2e_test/hld.png)


## Test lifecyle

1. build & deploy all instance based on docker-compose 
the script use --build flag to ensure we testing the latest app build

2. wait until the endpoint `http://localhost:5085` ready using [wait on](https://github.com/jeffbski/wait-on) package

3. run the test suite. all generated report based on this result step

4. remove deployment and revert the changes made during the test on file ``db.sqlite3``


you can check all this command in file ``test.sh``
