# Operating apps on Sealos

```bash
export KUBECONFIG=~/.sealos/kubeconfig     # once per session
```

## Inventory

```bash
python3 scripts/sealos-api.py instances                    # deployed template instances
kubectl get deploy,sts,pods                                # workloads
kubectl get clusters.apps.kubeblocks.io                    # databases + phase
kubectl get ingress -o custom-columns='NAME:.metadata.name,HOST:.spec.rules[0].host'
kubectl get all,ingress,cluster -l "cloud.sealos.io/deploy-on-sealos=<instance>"   # one instance's resources
kubectl get resourcequota -o yaml                          # namespace quota vs usage
```

## Triage a broken app

Work evidence-first; each step narrows the failure class:

```bash
kubectl get pods                                           # which pod, which state
kubectl describe pod <pod>                                 # events: pulls, scheduling, OOM
kubectl logs <pod> --all-containers --tail=100             # app-level errors
kubectl logs <pod> -p --tail=50                            # previous crash's logs
kubectl get events --field-selector type=Warning --sort-by=.lastTimestamp | tail -20
```

- `Pending` → describe shows quota or PVC problems.
- `ImagePullBackOff` / `exec format error` → image problem (tag, arch, auth).
- `CrashLoopBackOff` → logs; usually env/config/db-not-ready.
- Ready but URL broken → `kubectl get svc,ingress` port chain; then
  `kubectl exec <pod> -- wget -qO- localhost:<port>` (or `curl`) to test
  in-pod; if that works the Ingress/Service wiring is wrong.
- Database stuck → `kubectl get cluster <name> -o yaml | grep -A5 status:`;
  KubeBlocks clusters take 1-3 min to reach `Running`.

## Change and recover

```bash
kubectl set image deploy/<name> <container>=<image>        # new image
kubectl set env deploy/<name> KEY=value                    # tweak env
kubectl rollout restart deploy/<name>                      # restart
kubectl scale deploy/<name> --replicas=<n>                 # scale
kubectl rollout status deploy/<name>                       # watch it land
```

Pause/resume without deleting (what the UI pause button does): scale to 0 and
back. After any change, re-verify with `wait-app.sh`.

If a Path-B template needs the fix, edit the template file and fold the change
in — live-only fixes evaporate on the next deploy.

## Delete

Destructive — confirm with the user first, then verify afterwards.

```bash
python3 scripts/sealos-api.py delete <instance>            # instance + all resources
kubectl delete cluster.apps.kubeblocks.io <name>           # single database
kubectl get pvc                                            # storage costs money even when idle
kubectl delete pvc <name>                                  # only when its workload is gone
```

Instance deletion sweeps everything labeled with the instance (including
databases and StatefulSet PVCs). After deleting, confirm with
`kubectl get all -l "cloud.sealos.io/deploy-on-sealos=<instance>"` → empty.

## Cost hygiene

Running pods, KubeBlocks clusters, PVCs, and object-storage buckets all bill
against the account. After test deployments, delete the instance and check for
orphaned PVCs. When the user reports unexpected cost: `kubectl get
deploy,sts,cluster,pvc` and look for forgotten experiments.
