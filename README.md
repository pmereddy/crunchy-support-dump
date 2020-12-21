# crunchy-support-dump

## Description
The script creates a support dump for Crunchydata Postgres-Operator & PostgreSQL deployments 
in a namespace on Kubernetes. It collects kubernetes objects, logs and other metadata from the
objects corresponding to Crunchydata container solution only.

NOTE: Secrets and database data is not collected


## Pre-requisites
1. Valid login session to your Kubernetes cluster
2. kubectl or oc CLI in your PATH
3. Python3 in your PATH


## How to run it
To create a support dump for namespace "pgdb" and save it in $HOME/dumps/crunchy/pgdb_1221, run the following command
```
crunchy_support_dump.py -n pgdb -o $HOME/dumps/crunchy/pgdb_1221
```

## Example output
```
2020-12-21 10:49:55,784 - INFO - ------------------------------------------------------------------------------
2020-12-21 10:49:55,784 - INFO - Crunchy support dump collector
2020-12-21 10:49:55,785 - INFO - NOTE: We gather metadata and pod logs only. (No data and k8s secrets)
2020-12-21 10:49:55,785 - INFO - ------------------------------------------------------------------------------
2020-12-21 10:49:56,308 - INFO - Saving support dump files in /home/pramodh/dumps/crunchy/pgdb_1221/crunchy_k8s_support_dump_20201221-104955
2020-12-21 10:49:56,877 - INFO - Collected version-info
2020-12-21 10:49:57,401 - INFO - Collected node-info
2020-12-21 10:49:58,120 - INFO - Collected namespace-info
2020-12-21 10:49:58,664 - INFO - Collected k8s events
2020-12-21 10:49:59,130 - INFO - Collected pvc-list
2020-12-21 10:49:59,616 - INFO - Collected configmap-list
2020-12-21 10:49:59,618 - INFO - Collecting API resources:
2020-12-21 10:50:00,889 - INFO -   + pods
2020-12-21 10:50:02,088 - INFO -   + ReplicaSet
2020-12-21 10:50:03,184 - INFO -   + Deployment
2020-12-21 10:50:04,133 - INFO -   + Services
2020-12-21 10:50:05,096 - INFO -   + Routes
2020-12-21 10:50:06,784 - INFO -   + Ingress
2020-12-21 10:50:08,782 - INFO -   + pvc
2020-12-21 10:50:10,305 - INFO -   + configmap
2020-12-21 10:50:11,263 - INFO -   + pgreplicas
2020-12-21 10:50:12,367 - INFO -   + pgclusters
2020-12-21 10:50:13,417 - INFO -   + pgpolicies
2020-12-21 10:50:14,467 - INFO -   + pgtasks
2020-12-21 10:50:14,489 - INFO - Collecting last 2 PG logs (This could take a while)
2020-12-21 10:50:18,321 - INFO -   + pod:fcpdev-kziv-6db4dc878f-bjphj
2020-12-21 10:50:22,133 - INFO -   + pod:fcpdev-mwjx-7d4b985fd7-xhfvt
2020-12-21 10:50:22,136 - INFO - Collecting pod logs:
2020-12-21 10:50:23,873 - INFO -   + pod:backrest-backup-fcpdev-dgmj4, container:backrest
2020-12-21 10:50:25,031 - INFO -   + pod:fcpdev-backrest-shared-repo-6cb4f45fc4-5n9vg, container:database
2020-12-21 10:50:29,364 - INFO -   + pod:fcpdev-kziv-6db4dc878f-bjphj, container:database
2020-12-21 10:50:30,587 - INFO -   + pod:fcpdev-kziv-6db4dc878f-bjphj, container:collect
2020-12-21 10:50:31,491 - INFO -   + pod:fcpdev-kziv-6db4dc878f-bjphj, container:pgbadger
2020-12-21 10:50:33,201 - INFO -   + pod:fcpdev-mwjx-7d4b985fd7-xhfvt, container:database
2020-12-21 10:50:33,896 - INFO -   + pod:fcpdev-mwjx-7d4b985fd7-xhfvt, container:collect
2020-12-21 10:50:34,617 - INFO -   + pod:fcpdev-mwjx-7d4b985fd7-xhfvt, container:pgbadger
2020-12-21 10:50:36,030 - INFO -   + pod:monitoring-78547bb54-snpx9, container:prometheus
2020-12-21 10:50:36,788 - INFO -   + pod:monitoring-78547bb54-snpx9, container:alertmanager
2020-12-21 10:50:37,737 - INFO -   + pod:monitoring-78547bb54-snpx9, container:grafana
2020-12-21 10:50:39,016 - INFO -   + pod:pgadmin4-565f968ff4-vv9tk, container:pgadmin
2020-12-21 10:50:40,211 - INFO -   + pod:pgo-client-5fdccb64b5-4xkkr, container:pgo
2020-12-21 10:50:41,641 - INFO -   + pod:postgres-operator-f549db7fb-lw8hn, container:apiserver
2020-12-21 10:50:43,806 - INFO -   + pod:postgres-operator-f549db7fb-lw8hn, container:operator
2020-12-21 10:50:44,733 - INFO -   + pod:postgres-operator-f549db7fb-lw8hn, container:scheduler
2020-12-21 10:50:45,561 - INFO -   + pod:postgres-operator-f549db7fb-lw8hn, container:event
2020-12-21 10:50:45,563 - INFO - Collecting PG pod details:
2020-12-21 10:50:52,793 - INFO -   + pod:fcpdev-kziv-6db4dc878f-bjphj, container:database
2020-12-21 10:50:54,894 - INFO -   + pod:fcpdev-kziv-6db4dc878f-bjphj, container:collect
2020-12-21 10:50:56,380 - INFO -   + pod:fcpdev-kziv-6db4dc878f-bjphj, container:pgbadger
2020-12-21 10:51:05,579 - INFO -   + pod:fcpdev-mwjx-7d4b985fd7-xhfvt, container:database
2020-12-21 10:51:06,965 - INFO -   + pod:fcpdev-mwjx-7d4b985fd7-xhfvt, container:collect
2020-12-21 10:51:08,703 - INFO -   + pod:fcpdev-mwjx-7d4b985fd7-xhfvt, container:pgbadger
2020-12-21 10:51:09,572 - INFO - Archive file : /home/pramodh/dumps/crunchy/pgdb_1221/crunchy_k8s_support_dump_20201221-104955.tar.gz
2020-12-21 10:51:09,573 - INFO - ------------------------------------------------------------------------
2020-12-21 10:51:09,573 - INFO - Archive file size (bytes): 371042
2020-12-21 10:51:09,573 - INFO - Email the support dump to support@crunchydata.com
2020-12-21 10:51:09,573 - INFO - ------------------------------------------------------------------------

```
