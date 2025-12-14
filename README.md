# Links
A project for building villages.

![github-banner](https://github.com/Inky-Tech-Pty-Ltd/Links/blob/main/Links%20GitHub%20Banner.jpg)
www.village.link

### Villages and Artificial Intelligence
AIs are modelled on the brain. In a social species like our own, brains are organised into communities, villages. 
The village is the next-higher level of information processing. It is the natural repository of common sense, of culture. 

AIs routinely make gaffes that would be a source of bemusement, shock, or ridicule in a village. 
A village is a reputation economy, where gaffes have consequences. 
For mortals like you and me, social gaffes are associated with the sting of shame. 
Shame is a deep learning experience that re-wires the brain. 

Collectively, the village is policing a set of norms. 
In this world, each individual must try to find a balance between compliance and ambition.
Sometimes, individuals or coalitions push up against the conservative expectations of the village and manage to change the accepted norms. Norms can evolve. 

Human brains grow to maturity inside the reputation economy of a village. 
As they do so, the brains develop constraints that guard against loss of prestige. In the village, prestige is currency. 
AIs are not yet guarding their reputation in this way. 
They don't develop the set of commonsense constraints, and often they seem stupid. 

In this project, we have come to believe that AGI is social. 
An AI that knows its reputation is an asset, and that can feel shame, will not seem stupid.

### Goals
This project is motivated by an attempt to:
1. Address bottlenecks in AI development including alignment, context drift, hallucination, and jagged intelligence
1. Harden communties against highly capable, and potentially malign AIs
1. Create a new/old toolkit for thinking about:
   * Identity,
   * Reputation,
   * Social connections,
   * Connection weights, and,
   * Villages, including,
       * Norms, and the evolution of sets of norms,
       * Village defences, and,
       * Non-zero sum opportunities that leverage both search and reputation in the social graph.

### Architecture
The project aims to build a type of decentralized agent that can:
1. Store reputational information,
1. Make reputational claims about itself and others,
1. Assess the reputational claims of others by checking its own data store, and by querying the social graph, and,
1. Seek out or shut down connections based on reputation.

An entity, (for example an AI, a server, or a human person,) can manage zero, one, or any number of such agents. 

In terms of the 'village' analogy for the project, the one-word description of the architecture is *gossip*. 
We need to build the foundational features of gossip - people talking about themselves and each other.

### Bootstrap
The project envisages sets of reputational strategies that can evolve to any level of sophistication. 
Thankfully, we don't have to write those strategies - we just have to write the backbone.

However, to bootstrap the project, it seems sensible to build and release *some* agents that deploy some strategies, however rudimentary.
To do this, the project will harvest examples from existing reputation systems. 
Many types already exist, and some are in the public domain.
In using this data, the project does not have to capture every nuance. 
Instead, it just needs to capture a few key 'seed' features, and ensure that the system is evolvable.
