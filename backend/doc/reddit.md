Reddit
Arcade Optimized
Description: Enable agents to interact with Reddit.

Author: Arcade

Auth: User authorization via the Reddit auth provider

PyPI Version
License
Python Versions
Wheel Status
Downloads
The Arcade Reddit MCP Server provides a pre-built set of tools for interacting with Reddit. These tools make it easy to build agents and AI apps that can:

Submit text posts
Comment on posts
Reply to comments
Get posts (title and other metadata) in a subreddit
Get content (body) of posts
Get top-level comments of a post
Determine if a subreddit exists or is private
Get rules of a subreddit
Get the authenticated user’s username
Get posts by the authenticated user
Available Tools
These tools are currently available in the Arcade Reddit MCP Sever.

Tool Name	Description
Reddit.SubmitTextPost	Submit a text-based post to Reddit.
Reddit.CommentOnPost	Comment on a Reddit post.
Reddit.ReplyToComment	Reply to a Reddit comment.
Reddit.GetPostsInSubreddit	Gets posts titles, links, and other metadata in the specified subreddit
Reddit.GetContentOfPost	Get content (body) of a Reddit post.
Reddit.GetContentOfMultiplePosts	Get content (body) of multiple Reddit posts.
Reddit.GetTopLevelComments	Get the first page of top-level comments of a Reddit post.
Reddit.CheckSubredditAccess	Check whether a user has access to a subreddit, including whether it exists
Reddit.GetSubredditRules	Get the rules of a subreddit
Reddit.GetMyUsername	Get the authenticated user's username
Reddit.GetMyPosts	Get posts created by the authenticated user
If you need to perform an action that’s not listed here, you can get in touch with us to request a new tool, or create your own tools with the Reddit auth provider.

Reddit.SubmitTextPost

See Example
Submit a text-based post to a subreddit

Parameters

subreddit (string, required) The name of the subreddit to which the post will be submitted.
title (string, required) The title of the submission.
body (string, optional) The body of the post in markdown format. Should never be the same as the title.
nsfw (boolean, optional) Indicates if the submission is NSFW. Default is False.
spoiler (boolean, optional) Indicates if the post is marked as a spoiler. Default is False.
send_replies (boolean, optional) If true, sends replies to the user’s inbox. Default is True.
Reddit.CommentOnPost

See Example
Comment on a Reddit post.

Parameters

post_identifier (string, required) The identifier of the Reddit post. The identifier may be a Reddit URL, a permalink, a fullname, or a post id.
text (string, required) The body of the comment in markdown format.
Reddit.ReplyToComment

See Example
Reply to a Reddit comment

Parameters

comment_identifier (string, required) The identifier of the Reddit comment to reply to. The identifier may be a comment ID, a Reddit URL to the comment, a permalink to the comment, or the fullname of the comment.
text (string, required) The body of the reply in markdown format.
Reddit.GetPostsInSubreddit

See Example
Gets posts titles, links, and other metadata in the specified subreddit.

The time_range is required if the listing type is ‘top’ or ‘controversial’.

Parameters

subreddit (string, required) The name of the subreddit to fetch posts from.
listing (enum (SubredditListingType), optional) The type of listing to fetch. For simple listings such as ‘hot’, ‘new’, or ‘rising’, the time_range parameter is ignored. For time-based listings such as ‘top’ or ‘controversial’, the ‘time_range’ parameter is required. Default is ‘hot’.
limit (integer, optional) The maximum number of posts to fetch. Default is 10, max is 100.
cursor (str, optional) The pagination token from a previous call.
time_range (enum (RedditTimeFilter), optional) The time range for filtering posts. Must be provided if the listing type is ‘top’ or ‘controversial’. Otherwise, it is ignored. Defaults to ‘today’.
Reddit.GetContentOfPost

See Example
Get the content (body) of a Reddit post by its identifier.

Parameters

post_identifier (string, required) The identifier of the Reddit post. The identifier may be a Reddit URL, a permalink, a fullname, or a post id.
Reddit.GetContentOfMultiplePosts

See Example
Get the content (body) of multiple Reddit posts by their identifiers in a single request

Parameters

post_identifiers (list of strings, required) A list of identifiers of the Reddit posts. The identifiers may be Reddit URLs, permalinks, fullnames, or post ids.
Reddit.GetTopLevelComments

See Example
Get the first page of top-level comments of a Reddit post.

Parameters

post_identifier (string, required) The identifier of the Reddit post. The identifier may be a Reddit URL, a permalink, a fullname, or a post id.
Reddit.CheckSubredditAccess

See Example
Checks whether the specified subreddit exists and also if it is accessible to the authenticated user.

Parameters

subreddit (string, required) The name of the subreddit to check.
Reddit.GetSubredditRules

See Example
Gets the rules of the specified subreddit

Parameters

subreddit (string, required) The name of the subreddit for which to fetch rules.
Reddit.GetMyUsername

See Example
Gets the username of the authenticated user.

Reddit.GetMyPosts

See Example
Get posts that were created by the authenticated user sorted by newest first

Parameters

limit (integer, optional) The maximum number of posts to fetch. Default is 10, max is 100.
include_body (boolean, optional) Whether to include the body of the posts in the response. Default is True.
cursor (str, optional) The pagination token from a previous call.
Auth
The Arcade Reddit MCP Sever uses the Reddit auth provider to connect to users’ Reddit accounts.

With the Arcade Cloud Platform, there’s nothing to configure. Your users will see Arcade as the name of the application that’s requesting permission.

With a self-hosted installation of Arcade, you need to configure the Reddit auth provider with your own Reddit app credentials.

Reference
SubredditListingType
The type of listing to fetch.

HOT (string: “hot”): The hottest posts in the subreddit.
NEW (string: “new”): The newest posts in the subreddit.
RISING (string: “rising”): The posts that are trending up in the subreddit.
TOP (string: “top”): The top posts in the subreddit (time-based).
CONTROVERSIAL (string: “controversial”): The posts that are currently controversial in the subreddit (time-based).
RedditTimeFilter
The time range for filtering posts.

NOW (string: “NOW”)
TODAY (string: “TODAY”)
THIS_WEEK (string: “THIS_WEEK”)
THIS_MONTH (string: “THIS_MONTH”)
THIS_YEAR (string: “THIS_YEAR”)
ALL_TIME (string: “ALL_TIME”)
