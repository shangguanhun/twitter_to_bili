import time
from twitter_scraper import get_tweets
import pymysql
import os


# MySql数据库账号信息,需要提前创建好数据库
Host = os.environ.get('db_url')
User = os.environ.get('user')
Password = os.environ.get('password')
Port = 10044
DB = u'twitter'
BiliUser = os.environ.get('bili_user')
BiliPassword = os.environ.get('bili_password')

g_connection = None
g_connection_errno = 0

def connect_mysql():
    print("connect database")
    global g_connection
    global g_connection_errno
    try:
        g_connection = pymysql.connect(host=Host,
                                     user=User,
                                     password=Password,
                                     port=Port,
                                     db=DB,
                                     charset='utf8',
                                     cursorclass=pymysql.cursors.DictCursor)
        print("connect success" )
    except Exception as e:
        g_connection = None
        g_connection_errno = e
        print("connect database error:%s"%e)


twitter_url = 'https://twitter.com/'
cv_list ={'misawa_official':'三澤紗千香','azumi_waki':'和氣あず未','Kanon_Shizaki':'志崎樺音','kitoakari_1016':'鬼頭明里',
'INFO_shikaco':'久保ユリカ','Riko_kohara':'小原莉子','aimi_sound':'爱美','ayasa_ito':'伊藤彩沙','AyakaOhashi':'大橋彩香',
'toyotamoe':'豊田萌絵','_maeshima_ami':'前島亜美','InfoItomiku':'伊藤美来','marika_0222':'高野麻里佳','inoriminase':'水瀬いのり',
's_toshitai_o':'佐倉としたい大西','mimori_suzuko':'三森すずこ','aya_uchida':'内田彩','naobou_official':'東山奈央',
'tokui_sorangley':'徳井青空','MachicoOfficial':'machico','ReinaUeda_Staff':'上田麗奈','k_moeka_':'小泉萌香',
'RiEmagic':'村川梨衣','hanazawa_staff':'花澤香菜','satosatomi58':'佐藤聡美','nishiasuka':'西明日香','0812asumikana':'阿澄佳奈',
'hidaka_rina0615':'日高里菜','yukachiofficial':'井口裕香','nanjolno':'南條愛乃','LiSA_OLiVE':'LiSA','Yaskiyo_manager':'安野希世乃',
'TomoyoKurosawa':'黒沢ともよ','suzaki_aya':'洲崎綾','akekodao':'明坂聡美','rikachimalu':'長江里加'}

video_to_time_dict = {}
video_to_id_dict = {}
cv_to_name_dict = {}

def get_video_list_by_cv():
	video_url_list = []
	for tweet in get_tweets(cv_list):
		if len(tweet['entries']['videos'])>0:
			cv_url = tweet['cv_url']
			print('[+] 处理' + cv_url)
			tw_url = twitter_url + cv_url + '/status/' + tweet['tweetId']
			if(tw_url not in video_to_time_dict):
				video_url_list.append(tw_url)
				video_to_time_dict[tw_url] = cv_list[cv_url]  + str(tweet['time']) +' 转推 '
				video_to_id_dict[tw_url] = tweet['tweetId']
				cv_to_name_dict[tw_url] = cv_list[cv_url]

	return video_url_list

def down_and_up_load(url):
	from bilibiliupload import Bilibili
	from bilibiliupload import VideoPart
	import twitter_dl
	video = ''
	try:
		twitter_dl = TwitterDownloader(url)
		video = twitter_dl.download()
		print(video)
	except:
		print(url + 'is null')

	if len(video) > 0 :
		print('[+] upload' + cv_to_name_dict[url])
		b = Bilibili()
		b.login(BiliUser,BiliPassword)
		tags = ['声优']
		tags.append(cv_to_name_dict[url])
		b.upload(VideoPart(video, 'part_title', 'part_desc'),video_to_time_dict[url],152,tags,"立志于单推霓虹女声优，该视频为机器人自动爬取霓虹女声优推特转发,如需二次创作，标明推特源即可。若喜欢的cv未被收录，私聊本号~项目位于https://github.com/shangguanhun/twitter_to_bili，自取",source=url)

		path = video
		if os.path.exists(path):  # 如果文件存在
			os.remove(path)  
			print('[+] remove ' + path)

def upload_all_video():

	video_list = get_video_list_by_cv()
	if len(video_list) > 0:
		connect_mysql()
		with g_connection.cursor() as cursor:
			for voide_url in video_list:
				sql = "SELECT * FROM twitter_data WHERE twitter_id = %s" % video_to_id_dict[voide_url]
				#print(sql)
				results = cursor.execute(sql)
				if results == 0:
					down_and_up_load(voide_url)
					sql = "INSERT IGNORE INTO twitter_data(twitter_id) VALUES (%s)" % (video_to_id_dict[voide_url])
					print(sql)
					cursor.execute(sql)
					g_connection.commit()
					time.sleep(30)#睡眠30s

			g_connection.close()

#if __name__ == '__main__':	
def main_handler(event, context):
	upload_all_video()
	
	