# auguris

## Project Structure
```
TBD
```

## Getting Started

Install dev dependencies:
- Taskfile/
- pipenv

In order to run this project (so far):
```shell
pipenv shell
```
That should create a virtual environment for the project to which you should be able now to install all dependencies.
```shell
pipenv install
```

After that's done, you can run the tests to ensure the current version of the code is actually working:
```shell
task fetcher:test
```
That should run all tests with mocks for dependencies so you know that the code at least is working as it should.
