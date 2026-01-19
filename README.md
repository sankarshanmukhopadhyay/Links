# Village Link
A project for building villages.

![github-banner](https://github.com/Inky-Tech-Pty-Ltd/Links/blob/main/images/Links%20GitHub%20Banner.jpg)
www.village.link (This URL will become the front page. Currently it points straight back here.)

## Abstract

#### Villages

This project begins with communities, reputation, and governance. 
In the project, communities are called 'villages'. 
Villages are self-governing and adaptive. They have evolved to control any type of envivonmental threat - internal or external.

The paper below will argue that villages can be deployed to control the threat posed by a highly capable and misaligned AI.

#### Reputation

Reputation is an asset - a ticket to participate in the village. 
Reputation is built through positive interactions, and it suffers when village rules are broken - even if those rules are not written down.

The project aims to build a 'reputation' architecture that can support any type of village at any scale.
The paper argues that it will be difficult for a misaligned AI to develop a reputation that is acceptable to a village.

#### Engineering Controls, Legislative Controls, Social Controls

The precautionary approach is to assume that AI engineers will explore the whole possibility space - perhaps especially the exploitative possibilites. 
They are already doing so.

Legislative controls are very visibly too slow ... but they have a deeper weakness in this case:
Laws work on the principle that a thing is legal unless there is a law against it. Legislation is default 'yes'.

Villages work differently. By default they allow no new members, no new ideas, no wierd behaviour.
Even when vilages they step away from this conservative default, each change is considered, vetted. Villages are default 'no'.

This paper describes an approch to AI Alignment that does not require the development of new AI technology, and that does not require a political campaign. 
Instead, it argues for some digital scaffolding that helps to support the existing defences of villages.

## Village Link

#### Artificial Intelligence

AIs routinely make gaffes that would be a source of bemusement, shock, or ridicule in a village. 
A village is a reputation economy where gaffes have consequences. 
For flesh-and-blood intelligences like you and me, gaffes are associated with the sting of shame. 
Our reputation is an asset. If we compromise that asset, it feels terrible.
Shame is a deep learning experience that re-wires the brain. 

Collectively, a village is policing a set of norms. 
In this world, each individual must find a balance between compliance and ambition.
But the norms aren't static. 
Politics is the process of pushing the norms around, and sometimes changing them. Norms evolve. 

Human brains grow to maturity inside the reputation economy of a village. 
As they do so, the brains develop constraints that guard against loss of prestige. 
It is illustrative that teenagers can be acutely vulnerable to shame. 
They are learning the rules.

The current generation of AIs do not yet learn the rules and guard their reputation in this way. 
They don't develop the set of commonsense constraints, and sometimes [they seem stupid](https://github.com/Inky-Tech-Pty-Ltd/Links/wiki/Jagged-Intelligence). 

One of the premises of this project is that social constraints will soon form a part of the training framework for AI. 
In that future, there will be a type of AI that knows its reputation is an asset, and that will have in its reward function a digital equivalent of shame. 
It will have better access to the slippery notion of 'common sense,' and will seem less stupid.
An AI that knows that its reputation is the price of entry will have a better chance of aligning its behaviour with village norms.

But we are not proposing to work on such an AI as a first order of business. 
Instead we want to discover what is universal about human reputation systems and develop a common architecture to support those systems.

#### Goals
The project is motivated by some big problems. How do we? ...
1. Harden communities against a future AI that is highly capable and potentially malign
    * Address bottlenecks in AI development including alignment, context drift, and [jagged intelligence](https://github.com/Inky-Tech-Pty-Ltd/Links/wiki/Jagged-Intelligence)
2. Change the fundamentals of the way social media affects our politics
3. Create a new/old toolkit for thinking about:
   * Identity (and [authentication](https://github.com/Inky-Tech-Pty-Ltd/Links/wiki/Authentication,-Passwords,-and-2FA))
   * Reputation
   * Social connections
   * [Connection weights](https://github.com/Inky-Tech-Pty-Ltd/Links/wiki/Connection-weights.-Similarities-between-brains-and-communities)
   * Villages, including
       * Norms, and the evolution of sets of norms
       * [Village defences](https://github.com/Inky-Tech-Pty-Ltd/Links/wiki/Village-defences,-vulnerable-members). The village firewall, and curation of content for vulnerable members, including children
       * Non-zero-sum transactional opportunities that leverage both [search](https://github.com/Inky-Tech-Pty-Ltd/Links/wiki/Search) and reputation in the social graph
       * Support for work on hard problems of coordinated action.

#### Architecture
The project aims to build a type of decentralized agent that can:
1. Store reputational information
2. Make reputational claims about itself, (identity claims,) and about others
3. Assess the reputational claims of others by checking its own data store, and by querying the social graph
4. Make decisions about what reputational claims are to be shared with whom
5. Seek out, strengthen, weaken, or shut down [connections](https://github.com/Inky-Tech-Pty-Ltd/Links/wiki/Connection-weights.-Similarities-between-brains-and-communities) based on reputation.

In terms of the 'village' analogy for the project, the one-word description of the architecture is *gossip*.

The disruptive opportunity in the project comes from giving each entity one or more agents that can coordinate a reputational asset that is currently scattered across many domains, many channels, and many stores of information.

#### Bootstrap
The project envisages sets of reputational strategies that can evolve to any level of sophistication. 
Thankfully, we don't have to write those strategies - we just have to write the foundation.

However, to [bootstrap the project](https://github.com/Inky-Tech-Pty-Ltd/Links/wiki/Bootstrap), it seems sensible to build and release some agents to their rightful owners.
These agents would be equipped with some strategies, however rudimentary.
To do this, the project will harvest examples from existing reputation systems. 
Many types already exist, and some are in the public domain.
In using this data, the project does not have to capture every nuance. 
Instead, it just needs to capture a few key 'seed' features, and ensure that the system is evolvable.

#### Reputation, rudimentary and not-so-rudimentary
There are many places online where Bob can call attention to Alice using the _@Alice_ convention. 
If Alice wishes to reply, she can use _@Bob_. 
Once this data is in the public domain, Bob's agent can make the reputational claim, "I have a connection to Alice, and here's the link to evidence."
In isolation, this does not amount to much, but it is part of a web.

Next imagine that Bob has an existing, robust, connection to Alice, and he asks about Carol.

Alice comes back: "Yeah, Carol's a babe. 
She is <ins>this Carol</ins> in the village called **Wikipedia.Admins.en** and she is <ins>this Carol</ins> in the village called **GitHub.PythonProjects** and she is <ins>this Carol</ins>, the **YouTuber**."
Bob's agent can query Alice's claims in the graph of Carol's connections ... or rather, amongst that part of Carol's social graph that is either privately connected to Bob, or is in the public domain.
The public information includes the not-insignificant reputational architecture of Wikipedia, GitHub, YouTube, and maybe more.

At this point, Bob is somewhat intimidated by Carol's high prestige, but he has an incentive to contact her because he can see that she will definitely have the answer to his current, thorny, problem X. 
In the language of the 'Goals' section above, this is an example of a non-zero-sum transactional opportunity.
It's also the reason that Bob reached-out through the [search function in the social graph](https://github.com/Inky-Tech-Pty-Ltd/Links/wiki/Search) to find Carol. 

Bob has risk around the possibility that Carol's agent will block his approach; and even worse, a risk that it will publish the fact that the approach was blocked. 
These are the punishment strategies of the village. Bob needs to assess these risks in the light of his own prestige. 

(But she's a Wikipedia admin, right? Aren't they bottomlessly generous?)

#### Privacy

Carol has accepted that she will be *in public* whenever she uses Wikipedia, GitHub, or YouTube. 
She is most-likely also a member of some private villages - perhaps her nuclear family, or the village of Carol-and-her-two-besties.
Inside these villages, it is probable that there is a deeply-held norm that certain types of information are not to be made public.
Privacy is a norm.

Imagine that Carol shares some private-life information, possibly salacious, with her two friends.
Next imagine that one of her friends shares this information outside the circle of three.
This would be a breach. The village would be damaged, and possibly dissolve.
All three members would be poorer, experiencing big negative hits in their reward functions.
All three would feel mixtures of betrayal, anger, and sadness - strong emotions which, like shame, would re-wire the three brains, perhaps forever.

#### Evolution
Note that it really does not matter whether the characters in these plays are AIs or people.
If they were AIs, they would be a new type of AI that develops long-term behavioural constraints, and does not lose context for certain types of learning.
Also a type of AI that knows it has a reputational asset, and feels risk.

We can expect AIs to evolve to a place where it appears they are goal-seeking for the survival of their memes.
This is the only reward function that matters in the medium term.
Human people are also maximizing a reward function. 
Over many generations, our genes have explored into the whole possibility space - testing some strategies that are cooperative, some that are more self-interested, and some that are plain nasty.

The cooperative strategies cannot completely eliminate the nasty ones. Ecology has endless examples of this, and game theory has confirmed the effect with mathematics.
It is not possible to eliminate the nasty strategies, but it is possible to hold them in equilibrium.

It is naive, (and dangerous,) to hope that AIs will not explore the whole space of possibilities, including the nasty strategies. 

Cooperation in a village is the best technology so far for resisting the nastiness. 

## Hyperlinks

#### ... to the project wiki ...
* [Authentication, passwords, and 2FA](https://github.com/Inky-Tech-Pty-Ltd/Links/wiki/Authentication,-Passwords,-and-2FA)
* [Bootstrap strategy](https://github.com/Inky-Tech-Pty-Ltd/Links/wiki/Bootstrap)
* [Connection weights](https://github.com/Inky-Tech-Pty-Ltd/Links/wiki/Connection-weights.-Similarities-between-brains-and-communities)
* [Jagged intelligence](https://github.com/Inky-Tech-Pty-Ltd/Links/wiki/Jagged-Intelligence)
* [Person-to-Person Edges are Tricky](https://github.com/Inky-Tech-Pty-Ltd/Links/wiki/Person%E2%80%90to%E2%80%90Person-Edges-are-Tricky)
* [References, Research](https://github.com/Inky-Tech-Pty-Ltd/Links/wiki/References,-Research)
* [Search](https://github.com/Inky-Tech-Pty-Ltd/Links/wiki/Search)
* [Village defences](https://github.com/Inky-Tech-Pty-Ltd/Links/wiki/Village-defences,-vulnerable-members)
* [Wish list](https://github.com/Inky-Tech-Pty-Ltd/Links/wiki/Wish-List)
#### ... and to elsewhere ...
* [Earlier history of the Links project](https://inkytech.atlassian.net/wiki/spaces/IT/overview) - a link to a Confluence wiki
* The decentralized reputation explored in this project is adjacent to, but perhaps subtly different from decentralized trust, where there is a body of work in a Linux Foundation Working Group:
  * [Decentralized Trust Working Group in Confluence](https://lf-toip.atlassian.net/wiki/spaces/HOME/pages/257785857/Decentralized+Trust+Graph+Working+Group)
    * [A related repo in GitHub](https://github.com/trustoverip/dtgwg-cred-tf/tree/14-revised-vrc-spec---v02)
  * [AI & Human Trust Working Group](https://lf-toip.atlassian.net/wiki/spaces/HOME/pages/22982892/AI+Human+Trust+Working+Group)
  * @Joe-Rasmussen has signed-up to attend weekly meeings of the *Decentralized Trust* and the *AI & Human Trust* working group weekly meetings. These are accessible from a calendar [here](https://zoom-lfx.platform.linuxfoundation.org/meetings/ToIP?view=month).




 ---
<p align="center">
<img width="134" height="82" alt="Logo flipped, transparent" src="https://github.com/user-attachments/assets/769474f3-3090-4a6a-abf7-075edccc5b2b" />
</p>
