#/u/GoldenSights
import praw
import time
import traceback

''' USER CONFIGURATION ''' 

USERNAME  = "gwsCOMBO"
#This is the bot's Username. In order to send mail,
#it must have some amount of Karma.
PASSWORD  = ""
#This is the bot's Password. 
USERAGENT = "/u/GoldenSights Assigns Rank Flair and Sends Mod Mail"
#This is a short description of what the bot does.
#For example "/u/GoldenSights' Newsletter bot"
SUBREDDIT = "GoneWildSmiles"
#This is the sub or list of subs to scan for new posts.
#For a single sub, use "sub1".
#For multiple subreddits, use "sub1+sub2+sub3"
WAIT = 600
#The number of seconds between cycles. Bot is completely inactive during
#this time.

COMMENT_SHORT = "***%s*** *+%d Star%s*"
# The comment template for users who gain stars

COMMENT_LONG = """
***%s*** *+%d Star%s*

Make sure you [**Verify**](http://www.reddit.com/r/GoneWildSmiles/wiki/verification) to unlock your 
[**Star Flair**](http://www.reddit.com/r/GoneWildSmiles/wiki/stars) and become eligible 
to earn the Smile of the Week and Miss Smile awards! :D
"""
# Comment template for users who have not verified to receive star flair

MULTI_SUBREDDIT_RANK = False
#If you entered a single subreddit in SUBREDDIT, you can ignore this.
#If you entered multiple:
#	True = Posts are ranked relative to all the subreddits combined
#	False = Each subreddit is managed individually

IGNORE_UNKNOWN = True
#If a post has a flair that is not part of the rank system, should
# we just leave the post alone?
#If False, that post's flair will be overwritten with a rank!

RANKINGS = {   1: "Ultra Smile!!!!!",
			  10: "Killer Smile!!!!",
			  25: "Awesome Smile!!!",
			  50: "Super Smile!!",
			 100: "Great Smile!"
		   }
#Flair text

RANKINGCSS = {1: "Ultra",
			  10: "Killer",
			  25: "Awesome",
			  50: "Super",
			  100: "Great"}
#Flair CSS class. Use empty quotes if you don't have any.

SEND_MODMAIL = False
#Send subreddit modmail when a post achieves a rank
MODMAIL_SUBJECT = "Automated post ranking system"
#The subjectline for the sent modmail
MODMAIL_BODY = """
_username_ has just earned rank _ranktext_ on their
post ["_posttitle_"](_postlink_)
"""
#This is the modmail message
#Post information can be insterted into the message with these injectors
# _posttitle_ : Post title
# _postid_    : Post ID number
# _postlink_  : Post permalink
# _ranktext_  : Rank text
# _rankvalue_ : Rank value
# _username_  : Post author
#If you would like more injectors, please message me.

''' All done! '''

# Automatic preparation
RANKINGS_REVERSE = {}
for key in RANKINGS:
	val = RANKINGS[key].lower()
	RANKINGS_REVERSE[val] = key

RANKKEYS = sorted(list(RANKINGS.keys()))
MAXRANK = RANKKEYS[-1]

if MULTI_SUBREDDIT_RANK or '+' not in SUBREDDIT:
	SUBREDDIT_L = [SUBREDDIT]
else:
	SUBREDDIT_L = SUBREDDIT.split('+')

try:
	import bot
	USERNAME = bot.uG
	PASSWORD = bot.pG
	USERAGENT = bot.aG
except ImportError:
	pass
# /Automatic preparation

print('Logging in')
r = praw.Reddit(USERAGENT)
r.login(USERNAME, PASSWORD)
del PASSWORD

def scanSub():
    print('Searching '+ SUBREDDIT + '.')
    subreddit = r.get_subreddit(SUBREDDIT)
    posts = subreddit.get_top_from_all(limit=MAXRANK)
    for post in posts:
        try:
            pauthor = post.author.name
        except AttributeError:
            print(post.id, 'is being removed')
            post.remove()
            print('\tDone')

def manageranks():
	''' Ties it all together. '''
	for subreddit in SUBREDDIT_L:
		print('Getting posts from /r/%s' % subreddit)
		subreddit = r.get_subreddit(subreddit)
		topall = subreddit.get_top_from_all(limit=MAXRANK)
		topall = list(topall)
		for position in range(len(topall)):
			post = topall[position]
			position += 1
			# Add 1 because indices start at 0 and humans start at 1

			print(post.id, "Position: %d" % position)
			
			actual_flair = post.link_flair_text
			suggested = get_rank_from_pos(position)
			suggested_rank = suggested[0]
			suggested_flair = suggested[1]
			suggested_css = RANKINGCSS.get(suggested_rank, "")
			# Tries to get the CSS class and uses "" if it can't find it.

			if flair_is_better(new=suggested_flair, old=actual_flair):
				print('\tNew flair: %s' % suggested_flair)
				post.set_flair(flair_text=suggested_flair, flair_css_class=suggested_css)
				if actual_flair:
					actual_rank = RANKINGS_REVERSE[actual_flair.lower()]
					rankjump = RANKKEYS.index(actual_rank) - RANKKEYS.index(suggested_rank)
				else:
					rankjump = len(RANKKEYS) - RANKKEYS.index(suggested_rank)
				try:
					pauthor = post.author.name
				except:
					print('\tAuthor is deleted. Removing post.\n')
					post.remove()
					continue
				print('\tAwarding %d stars to %s' % (rankjump, pauthor))

				try:
					userflair = subreddit.get_flair(pauthor)
					userflaircss = userflair['flair_css_class']
					userflairtext = userflair['flair_text']
					# "But why don't you use the author_flair_text attribute of the post?"
					# This method ensures that if a users earns two flairs during this run, 
					# we increment their flair twice properly, instead of adding x+y=z twice.
				except:
					userflaircss = post.author_flair_css_class
					userflairtext = post.author_flair_text
					# Fallback for testing, etc.

				newflair = incrementflair(userflaircss, rankjump)
				subreddit.set_flair(pauthor, flair_css_class=newflair, flair_text=userflairtext)
				print('\told: css: %s, text: %s' % (userflaircss, userflairtext))
				print('\tnew: css: %s, text: %s' % (newflair, userflairtext))
				try:
				    int(newflair)
				    # If this passes, then the flair obviously contains only digits.
				    # It does not contain "star"
				    commenttext = COMMENT_LONG % (suggested_flair, rankjump, "s!" if rankjump > 1 else "!")
				except ValueError:
				    # The flair contains words, give them the short message
				    commenttext = COMMENT_short % (suggested_flair, rankjump, "s!" if rankjump > 1 else "!")

				starcomment = post.add_comment(commenttext)
				starcomment.distinguish()
				
				print("\tWriting comment:", commenttext)

				if SEND_MODMAIL:
					compose_modmail(post, suggested_flair, suggested_rank)
					pass
			print()

def get_rank_from_pos(position):
	''' Given a position in a listing, return the appropriate rank '''
	for rankkey in RANKKEYS:
		if rankkey >= position:
			return [rankkey, RANKINGS[rankkey]]

def flair_is_better(new, old):
	''' Compare whether the newer flair is better than the older flair '''
	newrank = RANKINGS_REVERSE[new.lower()]

	if old == "" or old is None:
		print('\tNew:%d, Old: None!' % (newrank))
		#Post has no flair yet. Anything is better
		return True
	try:
		oldrank = RANKINGS_REVERSE[old.lower()]
	except KeyError:
		if IGNORE_UNKNOWN:
			print('\t"%s" is not a recognized rank. Ignoring' % old)
			return False
		print('\t"%s" is not a recognized rank. Overwriting' % old)
		return True

	print('\tNew:%d, Old:%d' % (newrank, oldrank))
	if newrank < oldrank:
		print('\tBetter')
		return True
	print('\tNot better')
	return False

def compose_modmail(post, new, newrank):
	print('\tWriting modmail')
	subreddit = '/r/' + post.subreddit.display_name
	try:
		author = post.author.name
	except AttributeError:
		author = "[deleted]"

	message = MODMAIL_BODY
	message = message.replace('_posttitle_', post.title)
	message = message.replace('_postid_', post.id)
	message = message.replace('_postlink_', post.short_link)
	message = message.replace('_ranktext_', new)
	message = message.replace('_rankvalue_', str(newrank))
	message = message.replace('_username_', author)

	r.send_message(subreddit, MODMAIL_SUBJECT, message)

def incrementflair(flair, jump=1):
	if not flair or flair == "":
		return "%02d" % jump
	try:
		star = "star" in flair
		f = flair.replace("star", "")
		f = int(f)
	except ValueError:
		print("\tNon-numerical:", flair)
		return flair
	f += jump
	f = "%02d" % f
	if star:
		f += "star"
	return f

while True:
	try:
		scanSub()
		manageranks()		
	except Exception:
		traceback.print_exc()
	print('Sleeping %d seconds\n' % WAIT)
	time.sleep(WAIT)
