# Links
A project for building villages.

![github-banner](https://github.com/Inky-Tech-Pty-Ltd/Links/blob/main/images/Links%20GitHub%20Banner.jpg)
www.village.link (This URL will become the front page. Currently it points straight back here.)

### Villages and Artificial Intelligence
AIs are modelled on the brain. In a social species like our own, brains are organised into communities, into villages. 
The village is the next-higher-up level of information processing after the brain. It is the natural repository of common sense, of culture.
When we operate inside a village, we have a sense of being part of something bigger.

AIs routinely make gaffes that would be a source of bemusement, shock, or ridicule in a village. 
A village is a reputation economy where gaffes have consequences. 
For flesh-and-blood intelligences like you and me, gaffes are associated with the sting of shame. 
Our reputation is an asset. If we compromise that asset, it feels terrible.
Shame is a deep learning experience that re-wires the brain. 

Collectively, the village is policing a set of norms. 
In this world, each individual must find a balance between compliance and ambition.
Sometimes, ambitious individuals or coalitions of individuals push up against the established culture and change it. Norms evolve. 

Human brains grow to maturity inside the reputation economy of a village. 
As they do so, the brains develop constraints that guard against loss of prestige. 
It is illustrative that teenagers can be acutely vulnerable to shame. 
They are learning the rules.

The current generation of AIs do not yet guard their reputation in this way. 
They don't develop the set of commonsense constraints, and often [they seem stupid](https://github.com/Inky-Tech-Pty-Ltd/Links/wiki/Jagged-Intelligence). 

One of the premises of this project is that social constraints will soon form a part of the training framework for AI. 
We believe the future will include a type of AI that knows its reputation is an asset, and that will have in its reward function a digital equivalent of shame. 
We believe such an AI will have better access to the slippery notion of 'common sense'. 
We think such an AI will seem less stupid, and is a better chance of aligning its behaviour with village norms.

But we are not proposing to work on such an AI as a first order of business. 
Instead we want to discover what is universal about human reputation systems and develop a common architecture to support those systems.

### Goals
The project is motivated by an attempt to:
1. Harden communities against a future AI that is highly capable and potentially malign
2. Address bottlenecks in AI development including alignment, context drift, and [jagged intelligence](https://github.com/Inky-Tech-Pty-Ltd/Links/wiki/Jagged-Intelligence)
1. Create a new/old toolkit for thinking about:
   * Identity (and [authentication](https://github.com/Inky-Tech-Pty-Ltd/Links/wiki/Authentication,-Passwords,-and-2FA))
   * Reputation
   * Social connections
   * [Connection weights](https://github.com/Inky-Tech-Pty-Ltd/Links/wiki/Connection-weights.-Similarities-between-brains-and-communities)
   * Villages, including
       * Norms, and the evolution of sets of norms
       * [Village defences](https://github.com/Inky-Tech-Pty-Ltd/Links/wiki/Village-defences,-vulnerable-members), including the curation of content for vulnerable members. (Curation for children is an instance of a norm)
       * Non-zero-sum transactional opportunities that leverage both [search](https://github.com/Inky-Tech-Pty-Ltd/Links/wiki/Search) and reputation in the social graph
       * Support for work on hard problems of coordinated action.

### Architecture
The project aims to build a type of decentralized agent that can:
1. Store reputational information
2. Make reputational claims about itself, (identity claims) and about others
3. Assess the reputational claims of others by checking its own data store, and by querying the social graph
4. Make decisions about what reputational claims are to be shared with whom
5. Seek out, strengthen, weaken, or shut down [connections](https://github.com/Inky-Tech-Pty-Ltd/Links/wiki/Connection-weights.-Similarities-between-brains-and-communities) based on reputation.

An entity, (for example an AI, a server, or a human person,) can manage zero, one, or any number of such reputational agents. 

In terms of the 'village' analogy for the project, the one-word description of the architecture is *gossip*.

### Bootstrap
The project envisages sets of reputational strategies that can evolve to any level of sophistication. 
Thankfully, we don't have to write those strategies - we just have to write the foundation.

However, to bootstrap the project, it seems sensible to build and release some agents to their rightful owners.
These agents would be equipped with some strategies, however rudimentary.
To do this, the project will harvest examples from existing reputation systems. 
Many types already exist, and some are in the public domain.
In using this data, the project does not have to capture every nuance. 
Instead, it just needs to capture a few key 'seed' features, and ensure that the system is evolvable.

### Reputation, rudimentary and not-so-rudimentary
There are many places online where Bob can call attention to Alice using the _@Alice_ convention. 
If Alice wishes to reply, she can use _@Bob_. 
Once this data is in the public domain, Bob's agent can make the reputational claim, "I have a connection to Alice, and here's the link to evidence."
In isolation, this does not amount to much, but it is part of a web.

Next imagine that Bob has an existing, robust, connection to Alice, and he asks about Carol.

Alice comes back: "Yeah, Carol's a babe. 
She is <ins>this Carol</ins> in the village called **Wikipedia.Admins.en** and she is <ins>this Carol</ins> in the village called **GitHub.PythonProjects** and she is <ins>this Carol</ins>, the **YouTuber**."
Bob's agent can query Alice's claims in the graph of Carol's connections ... or rather, amongst that part of Carol's social graph that is either privately connected to Bob, or is in the public domain.
The public information includes the not-insignificant reputational architecture of Wikipedia, GitHub, YouTube, and maybe more.

At this point, Bob is somewhat intimidated by Carol's high prestige, but he has an incentive to contact her because he can see that she will definitely have the answer to his current, thorny, problem X - that is why he accessed the [search function](https://github.com/Inky-Tech-Pty-Ltd/Links/wiki/Search) through Alice. 
Also that if he can establish a connection with Carol it will bolster his own reputation.

Bob has risk around the possibility that Carol's agent will block his approach; and even worse, a risk that it will publish the fact that the approach was blocked. 
These are the punishment strategies of the village. Bob needs to assess these risks in the light of his own prestige. 

(But she's a Wikipedia admin, right? Aren't they bottomlessly generous?)

### Privacy

Carol has accepted that she will be *in public* whenever she uses Wikipedia, GitHub, or YouTube. 
She is most-likely also a member of some private villages - perhaps her nuclear family, or the village of Carol-and-her-two-besties.
Inside these villages, it is probable that there is a deeply-held norm that certain types of information are not to be made public.
Privacy is a norm.

Imagine that Carol's shares information about her primary intimate relationship with her two friends.
Next imagine that one of her friends shares this information outside the circle of three.
This would be a breach. The village would be damaged, and possibly dissolve.
All three members would be poorer, and all three would feel mixtures of betrayal, anger, and sadness - strong emotions which, like shame, would re-wire the three brains, perhaps forever.

### Evolution
Note that it really does not matter whether the characters in these plays are AIs or people.
If they were AIs, they would be a new type of AI that develops long-term behavioural constraints and does not lose context for certain types of learning.
Also a type of AI that knows it has a reputational asset, and feels risk.

We can expect AIs (and, of course, people) to evolve to a place where it appears they are goal-seeking for the survival of their memes (or genes).
This is the ultimate reward function. 
Both genes and memes need media and energy - resources where the village is guarding the store.

### Links
#### To the project wiki ...
* [Authentication, passwords, and 2FA](https://github.com/Inky-Tech-Pty-Ltd/Links/wiki/Authentication,-Passwords,-and-2FA)
* [Connection weights](https://github.com/Inky-Tech-Pty-Ltd/Links/wiki/Connection-weights.-Similarities-between-brains-and-communities)
* [Jagged intelligence](https://github.com/Inky-Tech-Pty-Ltd/Links/wiki/Jagged-Intelligence)
* [References](https://github.com/Inky-Tech-Pty-Ltd/Links/wiki/References)
* [Search](https://github.com/Inky-Tech-Pty-Ltd/Links/wiki/Search)
* [Village defences](https://github.com/Inky-Tech-Pty-Ltd/Links/wiki/Village-defences,-vulnerable-members)
* [Wish list](https://github.com/Inky-Tech-Pty-Ltd/Links/wiki/Wish-List)
#### And to elsewhere ...
* [Earlier history of the project](https://inkytech.atlassian.net/wiki/spaces/IT/overview) - a link to a Confluence wiki
* The decentralized reputation explored in this project is adjacent to, but perhaps subtly different from decentralized trust, where there is a significant body of existing work:
  * [Decentralized Trust Working Group in Confluence](https://lf-toip.atlassian.net/wiki/spaces/HOME/pages/22985064/All+Members+Meeting+Page)
  * [AI & Human Trust Working Group](https://lf-toip.atlassian.net/wiki/spaces/HOME/pages/22982892/AI+Human+Trust+Working+Group)
  * [A related repo in GitHub](https://github.com/trustoverip/dtgwg-cred-tf/tree/14-revised-vrc-spec---v02)
  * @Joe-Rasmussen has signed-up to attend weekly meeings of the *Decentralized Trust* and the *AI & Human Trust* working group weekly meetings. These are accessible from a calendar [here](https://zoom-lfx.platform.linuxfoundation.org/meetings/ToIP?view=month).
