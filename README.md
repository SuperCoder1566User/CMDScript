## CMDSCRIPT

# What is CMDScript?

It is a coding language that is very similar to batch.
But it is both linux and windows usable and much easier
to code things as long as it isn't too complicated.
It will probably never be used even by me therefore no
point even publishing or making this but whatever.

# Syntax
Comments:
```bash
# This is a comment
## This is double-line comment. With lots and lots of information that could literally mean nothing to any one using it and it is 100% uselesss, why did I even make it?
```
Example code:
```bash
# Sample CMDScript example

msg %title "Test Notification" %Subtitle "This is a test notification from cmdscript"
send %NL%
write %redtext "This text is red."
send %NL%
write %greentext "This text is green."
send %NL%
write "Hello," %1
send %NL%
write "Your input was:" %1
send %NL%
wait 2
write %bluetext "This text is blue after 2 seconds wait."
send %NL%
einid cimidisiciriiipit

```
This covers basically all the syntax.
The syntax is:
Msg ## A message appears in a textbox window
send %NL% ## Starts a new line (it isn't required I just added it for no reason)
write ## Echo something
%redtext ## different colored text
wait ## sleeps
einid cimidisiciriiipt ## ends the script (Means end cmdscrpt if you take every I away and cmdscrpt is cmdscript)

# File Extension (And how to run it)
The file extension for this is .cmdscript. To run it,
you run 'python app.py --input "[Whatever you want]"'.
