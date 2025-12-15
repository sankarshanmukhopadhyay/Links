# Links
A project for building villages.

![github-banner](https://github.com/Inky-Tech-Pty-Ltd/Links/blob/main/Links%20GitHub%20Banner.jpg)
www.village.link

### Villages and Artificial Intelligence
AIs are modelled on the brain. In a social species like our own, brains are organised into communities, into villages. 
The village is the next-higher-up level of information processing after the brain. It is the natural repository of common sense, of culture. 

AIs routinely make gaffes that would be a source of bemusement, shock, or ridicule in a village. 
A village is a reputation economy, where gaffes have consequences. 
For flesh-and-blood intelligences like you and me, gaffes are associated with the sting of shame. 
Our reputation is an asset. If we conpromise that asset, it feels terrible.
Shame is a deep learning experience that re-wires the brain. 

Collectively, the village is policing a set of norms. 
In this world, each individual must find a balance between compliance and ambition.
Sometimes, individuals or coalitions of individuals push up against the conservative expectations of the village and manage to change the accepted norms. Norms can evolve. 

Human brains grow to maturity inside the reputation economy of a village. 
As they do so, the brains develop constraints that guard against loss of prestige. In a village, prestige is currency. 
AIs are not yet guarding their reputation in this way. 
They don't develop the set of commonsense constraints, and often they seem stupid. 

Part of the premise of this project is that social constrains will form a useful training franework for AI. 
We believe the future will include a type of AI that knows its reputation is an asset, and that will have a digital equivalent of shame as part of its reward function. 
We believe such an AI will have better access to the slippery notion of 'common sense'. We think such an AI will seem less stupid, and is a better chance if aligning its behaviour with village norms.

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
       * Village defences
       * Non-zero sum opportunities that leverage both search and reputation in the social graph.

### Architecture
The project aims to build a type of decentralized agent that can:
1. Store reputational information
1. Make reputational claims about itself and others
1. Assess the reputational claims of others by checking its own data store, and by querying the social graph
1. Seek out or shut down connections based on reputation.

An entity, (for example an AI, a server, or a human person,) can manage zero, one, or any number of such agents. 

In terms of the 'village' analogy for the project, the one-word description of the architecture is *gossip*.

### Bootstrap
The project envisages sets of reputational strategies that can evolve to any level of sophistication. 
Thankfully, we don't have to write those strategies - we just have to write the backbone.

However, to bootstrap the project, it seems sensible to build and release *some* agents that deploy some strategies, however rudimentary.
To do this, the project will harvest examples from existing reputation systems. 
Many types already exist, and some are in the public domain.
In using this data, the project does not have to capture every nuance. 
Instead, it just needs to capture a few key 'seed' features, and ensure that the system is evolvable.
