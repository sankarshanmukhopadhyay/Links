# Links
A project for building villages.

www.village.link

### Villages and AIs
Artificial Intelligences (AIs) are modelled on the brain. In a social species like our own, brains are organised into communities, villages. 
The village is the next-higher level of information processing. It is the natural repository of common sense, of culture. 

AIs routinely make gaffes that would be a source of bemusement, shock, or ridicule in a village. 
Villages are reputation economies where gaffes have consequences. For people, gaffes are associated with the sting of shame. 
Shame is a deep learning experience that re-wires the brain.

Collectively, the village is policing a set of norms. 
In this world, each individual must try to find a balance between compliance and ambition.
Sometimes individuals push up against the expectations of the village and manage to change the accepted norms. Norms can evolve. 

Human brains grow to maturity inside the reputation economy of a village. 
As they do so, the brains develop constraints that guard against loss of prestige - the currency of the village. 
AIs are not yet guarding their reputation in this way. 
They don't develop the set of commonsense constraints, and often they seem stupid. In the project, we have come to believe that AGI is social.

### Goals
This project is motivated by an attempt to:
- Address bottlenecks in AI development including alignment, context drift, and jagged intelligence
- Harden human communties against highly capable, and potentially malign AIs
- Create a new/old toolkit for thinking about:
  - Identity
  - Reputation
  - Social connection
  - Connection weights, and
  - Villages, including:
    - Norms and the evolution of sets of norms
    - Village defences, and
    - Village opportunity, leveraging search in the social graph.

### Architecture
The project aims to build a type of decentralized agent that can:
1. Store reputational information;
1. Make claims about its own reputation; and,
1. Assess the reputational claims of others by checking its own store, and by querying the social graph.

An entity, (like an AI, a server, or a human person,) can manage zero, one, or any number of such agents. 

In terms of the 'village' analogy for the project, the one-word description of the architechture is *gossip*. 
We need to build the foundational features of gossip - people talking about themselves, people talking about people.

### Bootstrap
The project envisages sets of reputational strategies that can evolve to any level of complexity. 
Thankfully, we don't have to write those strategies - we just have to write the backbone.

However, to bootstrap the project, it seems sensible to build and release *some* agents that deploy some strategies, however rudimentary.
To do this, the project will harvest examples from existing reputation systems. 
Many types already exist, and some are in the public domain.
In using this data, the project does not have to capture every nuance. 
Instead, it just needs to capture a few key 'seed' features, and ensure that the system is evolvable.
