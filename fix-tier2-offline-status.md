# Fix: Tier 2 Offline Status in Verge Cluster

## Problem

After adding a 7th host to the Verge cluster with 2x 15TB disks assigned to Tier 2,
the tier is showing as **Offline** with 0.0 / 14.0TB used/capacity and 0/s read/write rates.

## Root Cause

VergeOS vSAN requires each tier to have physical disks present on **at least 2 nodes**
to come online. This is a redundancy requirement — the distributed storage engine needs
a minimum of 2 fault domains (nodes) to maintain data replication and availability.

In this case, Tier 2 disks were only installed on **one host** (the 7th host), so the
vSAN cannot form a redundant storage pool and marks the tier as Offline.

| Tier   | Status  | Reason                                      |
|--------|---------|---------------------------------------------|
| Tier 0 | Online  | Disks spread across multiple nodes           |
| Tier 1 | Online  | Disks spread across multiple nodes           |
| Tier 2 | Offline | Disks exist on only 1 node (host #7)         |

## Resolution

Add Tier 2 disks to **at least one additional host** in the cluster. Once a second node
contributes disks to Tier 2, the tier will transition to Online and begin accepting I/O.

### Steps

1. Install physical disk(s) (preferably matching 15TB capacity) on a second host in the cluster.
2. In the VergeOS UI, assign the new disk(s) to **Tier 2**.
3. Wait for the vSAN to detect the new disks and resync.
4. Verify Tier 2 status changes from Offline to **Online**.

## Notes

- For production workloads, it is recommended to have Tier 2 disks on **3 or more nodes**
  to ensure continued availability if one node goes down.
- The 14.0TB reported capacity (from 2x 15TB raw) reflects formatted/usable capacity after
  filesystem overhead.
