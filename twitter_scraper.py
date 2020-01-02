import grequests
import re
from requests_html import HTMLSession, HTML
from datetime import datetime

def get_tweets(user_list):
    """Gets tweets for a given user, via the Twitter frontend API."""
    def err_handler(request, exception):
        print(request.url)
        print(exception)
    
    def gen_tweets(cv_url,r):
        try:
            html = HTML(html=r.json()['items_html'],
                        url='bunk', default_encoding='utf-8')
        except KeyError:
            raise ValueError(
                f'Oops! Either "{user}" does not exist or is private.')

        comma = ","
        dot = "."
        tweets = []
        for tweet in html.find('.stream-item'):
            text = tweet.find('.tweet-text')[0].full_text
            tweetId = tweet.find(
                '.js-permalink')[0].attrs['data-conversation-id']
            time = datetime.fromtimestamp(
                int(tweet.find('._timestamp')[0].attrs['data-time-ms'])/1000.0 + 8*60*60)#加8h使其显示cn时间
            interactions = [x.text for x in tweet.find(
                '.ProfileTweet-actionCount')]
            replies = int(interactions[0].split(" ")[0].replace(comma, "").replace(dot,""))
            retweets = int(interactions[1].split(" ")[
                            0].replace(comma, "").replace(dot,""))
            likes = int(interactions[2].split(" ")[0].replace(comma, "").replace(dot,""))
            hashtags = [hashtag_node.full_text for hashtag_node in tweet.find('.twitter-hashtag')]
            urls = [url_node.attrs['data-expanded-url'] for url_node in tweet.find('a.twitter-timeline-link:not(.u-hidden)')]
            photos = [photo_node.attrs['data-image-url'] for photo_node in tweet.find('.AdaptiveMedia-photoContainer')]
            
            videos = []
            video_nodes = tweet.find(".PlayableMedia-player")
            for node in video_nodes:
                styles = node.attrs['style'].split()
                for style in styles:
                    if style.startswith('background'):
                        tmp = style.split('/')[-1]
                        video_id = tmp[:tmp.index('.jpg')]
                        videos.append({'id': video_id})
            tweets.append({'tweetId': tweetId, 'time': time, 'text': text,'cv_url':cv_url,
                            'replies': replies, 'retweets': retweets, 'likes': likes, 
                            'entries': {
                                'hashtags': hashtags, 'urls': urls,
                                'photos': photos, 'videos': videos
                            }
                            })

        return tweets

    url_list = []
    task = []
    for user in user_list:
        url = f'https://twitter.com/i/profiles/show/{user}/timeline/tweets?include_available_features=1&include_entities=1&include_new_items_bar=true'
        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Referer': f'https://twitter.com/{user}',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/603.3.8 (KHTML, like Gecko) Version/10.1.2 Safari/603.3.8',
            'X-Twitter-Active-User': 'yes',
            'X-Requested-With': 'XMLHttpRequest'
        }
        rs = grequests.get(url, headers=headers,timeout = 3)
        task.append(rs)
    resp = grequests.map(task, size=64, exception_handler=err_handler)

    index = 0
    key_list = list(user_list.keys())
    for res in resp:
        tweets = gen_tweets(key_list[index],res)
        url_list = url_list + tweets

        index = index + 1

    return url_list
