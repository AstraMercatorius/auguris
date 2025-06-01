from behave import given, then

@given(u'a request is made for "{coin_pair}" data')
def step_ohlc_coin_request(context, coin_pair):
    assert context.foo == "bar"
    assert coin_pair == "BTC/USD"

@then(u'the raw data should be pushed in "{subject}" subject')
def step_subject_pushed(context, subject):
    context.loop.run_until_complete(context.js.publish(subject, b"data"))
    assert context.foo == "bar"
    assert subject == "market-data.raw.BTC-USD"
    sub = context.loop.run_until_complete(context.js.pull_subscribe("market-data.raw.>", "feature-engineering"))
    msgs = context.loop.run_until_complete(sub.fetch(1, timeout=1))
    assert len(msgs) == 1
    msgs[0].ack()
