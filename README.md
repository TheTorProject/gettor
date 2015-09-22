GetTor Revamp
=============

GetTor Revamp done during the Google Summer of Code 2014 for the Tor Project.
This repository continues to being used for improvements and further
development.

What is GetTor?
===============

GetTor was created as a program for serving Tor and related files over SMTP,
thus avoiding direct and indirect _censorship_ of Tor's software, in particular,
the Tor Browser Bundle (TBB). Users interacted with GetTor by sending emails
to a specific email address. After the user specified his OS and language,
GetTor would send him an email with an attachment containing the requested
package. This worked well for a while, but the bundles started to get too
large for being sent as attachments in most email providers. In order to fix
this, GetTor started to send (Dropbox) links instead of attachments.

What are the goals of the new GetTor?
=====================================

Here is a list of the main goals the new GetTor should accomplish:

 * Safe. Remember we are serving people under _heavy censorship_.
 * Easy to use. The fewer user interactions, the better.
 * Clean code. It should be clear to other developers/contributors how GetTor
 works and how it can be improved.
 * Automated. We should try to automate things as much as possible.
 * Language and provider friendly. It should be easy to support new languages
 and to add new providers for storing packages and generate links.


How does the new GetTor works?
==============================

Below are some specifications and core concepts on how the new GetTor works.

*Links files*: Currently links are saved in files with the '.links' extension,
using the ConfigParser format (RFC 882). A sample link file should look like
this:

--- BEGIN FILE ---

  [provider]
  name = CoolCloudProvider

  [key]
  fingerprint = AAAA BBBB CCCC DDDD EEEE FFFF GGGG HHHH IIII JJJJ

  [linux]
  en = Package (64-bit): https://cool.cloud.link64
	ASC signature (64-bit): https://cool.cloud.link64.asc
	Package SHA256 checksum (64-bit): superhash64,
	Package (32-bit): https://cool.cloud.link32
	ASC signature (32-bit): https://cool.cloud.link32.asc
	Package SHA256 checksum (32-bit): superhash32

  [windows]
  ...

  [osx]
  ...

--- END FILE ---

You can also check providers/dropbox.links for a better example.

*Core*: the heart of GetTor. Receives requests for links for a certain OS and
language and respond accordingly. It also presents an easy way for scripts
to create links file.

*SMTP*: Receives requests via email, process them, contact the core module if
necessary and respond to the user in the specified language. People can send
blank or dummy emails to it to receive a help message describing how to ask
for links. Email forwarding is used to redirect the emails to GetTor.

*XMPP*: Same as above, but via XMPP (account needed). It has been tested with
dukgo.com, jabber.ccc.de, riseup.net. It doesn't seem to be able to interact
with gtalk users.

*Twitter*: Receive requests via Twitter direct messages, contact the core module
if necessary and respond to the user in the specified language. Unfinished.

*DB*: Store anonymous info about the people that interact with GetTor in order
to keep count of the number of requests per person and avoid malicious users
that try to collapse the service. It also keeps count of how many requests
GetTor has received during its lifetime. A lot of other data was being saved
in the original gsoc project, but it was changed to save the minimum. 

*Blacklist*: Provide a mechanism to avoid flood and deny interaction to
malicious users.

*Providers scripts*: every supported provider should have a script to
automatically upload packages to 'the cloud' and create the corresponding
links files. The script should consider the following steps:

 * Upload the packages.
 * Get the sha256 checksum of the files uploaded.
 * Get the PGP key fingerprint that signed the files.
 * Check for .asc file for every package uploaded.
 * Put all together in a '.link' file (using the core module).


What is the current status of the new GetTor?
=============================================

Deployed and working.


How can I help?
================

If you have ideas to improve GetTor and/or add new providers, please tell us!
I'm currently the lead developer on this, so if you have any comments/doubts/
ideas you can send me an e-mail to ilv _at_ riseup _dot_ net or ping me (ilv),
or sukhe or mrphs at #tor-dev in the OFTC IRC network. For openning tickets you
should use the trac[0] and select the GetTor component. Some neat ideas we
could use are the following:

 * Report bugs!
 * Create script for new providers, namely: Google Drive, Github. Check 
providers.txt
 * Create a new module for distributing links. Check distribution_methods.txt
 * Finish the Twitter module.
 * Propose code/behaviour improvements.
 * Update the specs.


References
===========

[0] https://trac.torproject.org/projects/tor/query?status=accepted&status=assigned&status=needs_information&status=needs_review&status=needs_revision&status=new&status=reopened&component=GetTor&col=id&col=summary&col=component&col=status&col=type&col=priority&col=milestone&order=priority

