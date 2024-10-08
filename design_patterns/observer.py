# Observer, behavioral design pattern

class YouTubeChannel:
    def __init__(self, channel_name):
        self._subscribers = []
        self._channel_name = channel_name

    def subscribe(self, subscriber):
        self._subscribers.append(subscriber)

    def unsubscribe(self, subscriber):
        self._subscribers.remove(subscriber)

    def upload_video(self, video_title):
        print(f"{self._channel_name} uploaded a new video: {video_title}")
        self.notify_subscribers()

    def notify_subscribers(self):
        for subscriber in self._subscribers:
            subscriber.update(self)


class Subscriber:
    def __init__(self, name):
        self._name = name

    def update(self, channel):
        print(f"{self._name} is notified of a new video from {channel._channel_name}")

# Create a YouTube channel and subscribers
channel = YouTubeChannel("TechTalk")
subscriber1 = Subscriber("Alice")
subscriber2 = Subscriber("Bob")

# Subscribe to the channel
channel.subscribe(subscriber1)
channel.subscribe(subscriber2)

# Upload a new video
channel.upload_video("How to build a Python web app")
