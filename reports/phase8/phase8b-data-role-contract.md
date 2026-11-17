# Phase8B approved data roles

P1 fits the weather/soil backbone only on 1995–2009 TRAIN; 2010–2014 Dev is accessed once after architecture/training choices are frozen. G1 failure for both registered architectures halts G2/G3.

P2 is explicitly a retrospective nested LOYO/LORO cross-fitted evaluation. The backbone is frozen. The four-dimensional low-rank spatial adapter with L2=10 uses only each outer training fold labels. Outer held-out labels score once; no prospective or untouched blind-test claim. Forty Former-Held-Out and four Public-Reused rows are separate. Raw 64-dimensional vectors stay in the numerical encoder only.

Approved by continue-ef655327bd618e46.md, attempt27. This resolves the missing contemporaneous 1995–2009 satellite data issue without pairing future embeddings with old weather.
