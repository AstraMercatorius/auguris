from typing import List
import behave
from nats.aio.msg import Msg

base_subject = "market-data.raw"

@behave.given(u'a request is made for "{coin_pair}" data')
def step_ohlc_coin_request(context, coin_pair: str):
    context.register_mock(f"{coin_pair.replace('/', '-')}.json", "/0/public/OHLC", "GET")
    # context.loop.run_until_complete(context.js.publish(f"{base_subject}.{coin_pair.replace('/', '-')}", b"data"))

@behave.then(u'the raw data should be pushed in "{subject}" subject')
def step_subject_pushed(context, subject):
    sub = context.loop.run_until_complete(context.js.pull_subscribe(subject, "feature-engineering_test"))
    msgs: List[Msg] = context.loop.run_until_complete(sub.fetch(1, timeout=3600))
    assert len(msgs) == 1
    msg = msgs[0]
    assert msg.data.decode("utf-8") != ""
    print(f"Message received {msg.data.decode('utf-8')}")
    msgs[0].ack()
