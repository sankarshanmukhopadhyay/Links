# Links
A project for building villages.

![github-banner](https://github.com/Inky-Tech-Pty-Ltd/Links/blob/main/Links%20GitHub%20Banner.jpg)
www.village.link (This URL will become the front page. Currently it points straight back here.)

### Villages and Artificial Intelligence
AIs are modelled on the brain. In a social species like our own, brains are organised into communities, into villages. 
The village is the next-higher-up level of information processing after the brain. It is the natural repository of common sense, of culture. 

AIs routinely make gaffes that would be a source of bemusement, shock, or ridicule in a village. 
A village is a reputation economy where gaffes have consequences. 
For flesh-and-blood intelligences like you and me, gaffes are associated with the sting of shame. 
Our reputation is an asset. If we compromise that asset, it feels terrible.
Shame is a deep learning experience that re-wires the brain. 

Collectively, the village is policing a set of norms. 
In this world, each individual must find a balance between compliance and ambition.
Sometimes, individuals or coalitions of individuals push up against the village consensus and manage to change its conservative expectations. Norms evolve. 

Human brains grow to maturity inside the reputation economy of a village. 
As they do so, the brains develop constraints that guard against loss of prestige. 
It is illustrative that teenagers can be acutely vulnerable to shame. 
They are learning the rules.

The current generation of AIs do not yet guard their reputation in this way. 
They don't develop the set of commonsense constraints, and often they seem stupid. 

One of the premises of this project is that social constraints will soon form a part of the training framework for AI. 
We believe the future will include a type of AI that knows its reputation is an asset, and that will have in its reward function a digital equivalent of shame. 
We believe such an AI will have better access to the slippery notion of 'common sense'. 
We think such an AI will seem less stupid, and is a better chance of aligning its behaviour with village norms.

But we are not proposing to work on such an AI as a first order of business. 
Instead we want to discover what is universal about human reputation systems and develop a common architecture to support those systems.

### Goals
This project is motivated by an attempt to:
1. Harden communities against a future AI that is highly capable and potentially malign
2. Address bottlenecks in AI development including alignment, context drift, and jagged intelligence
1. Create a new/old toolkit for thinking about:
   * Identity
   * Reputation
   * Social connections
   * Connection weights
   * Villages, including
       * Norms, and the evolution of sets of norms
       * Village defences, including the curation of content for vulnerable members (curation for children is a special case of a norm)
          * (Note that the project is envisaging a world where entities tend not to face the jungle of the internet alone. Instead, entities exist mostly within villages that have collective defences against the jungle. *All members* are vulnerable members. Content servers are entities with reputations - they may or may not be invited inside the village wall according to the norms of that village) 
       * Non-zero-sum transactional opportunities that leverage both search and reputation in the social graph
       * Support for work on hard problems of coordinated action.

### Architecture
The project aims to build a type of decentralized agent that can:
1. Store reputational information
1. Make reputational claims about itself, (identity claims) and about others
1. Assess the reputational claims of others by checking its own data store, and by querying the social graph
1. Seek out, strengthen, weaken, or shut down connections based on reputation.

An entity, (for example an AI, a server, or a human person,) can manage zero, one, or any number of such reputational agents. 

In terms of the 'village' analogy for the project, the one-word description of the architecture is *gossip*.

### Bootstrap
The project envisages sets of reputational strategies that can evolve to any level of sophistication. 
Thankfully, we don't have to write those strategies - we just have to write the backbone.

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
Bob's agent can query Alice's claims in the graph of Carol's connections ... or rather, amongst that part Carol's social graph that is also connected to Bob.
In assessing Alice's claims about Carol, Bob's agent also has access to the not-insignificant reputational architecture of Wikipedia, GitHub, YouTube, and maybe more.

At this point, Bob is somewhat intimidated by Carol, but he has an incentive to contact her because he can see that she will definitely have the answer to his current, thorny, problem X. 
Also that if he can establish a connection with her it will bolster his own reputation.
Bob has risk around the possibility that Carol's agent will block his approach; and even worse, a risk that it will publish the fact that the approach was blocked. 
These are the punishment strategies of the village. Bob needs to assess these risks in the light of his own prestige. 

(But she's a Wikipedia admin, right? Aren't they bottomlessly generous?)

### Privacy

Carol has accepted that she will be *in public* whenever she uses Wikipedia, GitHub, or YouTube. 
She is most-likely also a member of some private villages - perhaps her nuclear family, or the village of Carol-and-her-two-besties.
Inside these villages, it is probable that there is a deeply-held norm that certain types of information are not to be made public.
Privacy is a norm.

Imagine that one of Carol's besties shares intimate relationship information outside the village.
This would be a breach. The village would be damaged, and possibly dissolve. 
All three members would be poorer, and all three would feel mixtures of anger and sadness - strong emotions which, like shame, would re-wire the three brains, potentially forever.

Note that it really does not matter whether the characters in these plays are AIs or people. 
Whether digital life or wet life, our players are constrained by the reputation economy. 
Digital or wet, their ultimate needs are energy and media - resources where the network of connections is guarding the store.
