# auguris

## Testing

While personally I'm a huge advocate for TDD/BDD, and I have added a few tests for `/packages/market-data/ohlc-fetcher`, adding the mocks for `/packages/market-data/feature-engineering` was getting very hard and I really needed this to be running on my home-lab ASAP to take advantage of crypto moves.

I'm not proud of this decision, and when possible tests will be used to drive development.

On this project you'll find 2 interesting developments in this area, a `mock-server` that allows you to create mock responses for REST APIs, one that could be set up as part of the background needed for a test; the second thing is under the `/features` directory, in which a project has been set using `behave`. This is still a work in progress and it's ultimately what I want to use to describe the behavior of the entire system and list all of the features of this project, which is why `mock-server` was created as well.

Since this is not a client-facing app that needs to be 100% correct, I'm ok with the sacrifice that not doing proper BDD will come with. I just need this to be correct enough so I can start getting predictions out of the models and start generating data, probably also some orders on Kraken.

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
