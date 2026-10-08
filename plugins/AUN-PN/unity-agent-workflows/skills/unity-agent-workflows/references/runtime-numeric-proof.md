# Runtime Numeric Proof

Use after any visible-output patch fails, appears unchanged, lands in the wrong place, or is challenged with a screenshot. After a visible patch is challenged, static source reasoning is not enough.

Static source inspection is not runtime proof. Sub-agent reasoning is not runtime proof. Compile success is not visual proof. Screenshot estimation is not coordinate proof. Checker confidence is not proof without values.

## Runtime Numeric Proof Gate

Before another coordinate, focus, layout, marker, camera, safe-area, or fallback patch, collect concrete runtime values from Play Mode, Unity MCP/runtime hierarchy query, Device Simulator, Game view inspection, or temporary runtime logs:

```text
source object:
source parent chain:
source bounds: markerRect / visualRect / interactiveRect / logicRect
source canvas/root:
source canvas renderMode:
source canvas scaleFactor:
source camera:
destination object/root:
destination canvas/root:
destination canvas renderMode:
destination canvas scaleFactor:
destination camera:
conversion API path:
converted rect min/max:
converted center/size:
final drawn object:
final drawn position:
final drawn size/bounds:
active caller:
active runtime caller:
active asset/sprite/model name:
selector/factory result:
fallback path/value used:
runtime writer checked:
validation:
```

Missing source bounds, converted rect, final drawn rect, active caller, or active asset/sprite/model name is a FAIL when those values are relevant to the challenged visible behavior. On FAIL, stay read-only and return a runtime probe plan only.

## Repeated-Fix Flow

When the user says the result is still wrong:

1. Stop tuning constants.
2. Re-read the screenshot/target wording.
3. Re-run the Runtime Visible Output Hard Stop proof chain.
4. Run the Runtime Numeric Proof Gate before another patch.
5. Check duplicate names, inactive scene objects, cloned runtime objects, and parent-chain ambiguity.
6. Search runtime writers and refresh paths.
7. Check whether the edited script is in the compiled assembly.
8. Check whether scene/prefab overrides also need updating.
9. Patch only after numeric proof explains the mismatch.
10. Validate with Game view/device/screenshot proof when possible.

## Quantitative Spatial Accuracy Metrics (IoU & Tolerances)

Never accept subjective claims ("it looks aligned" or "close enough"). Verify spatial accuracy using **Intersection over Union (IoU / Jaccard Index)** (Pascal VOC / COCO benchmark standard):

$$\text{IoU}(A, B) = \frac{\text{Area}(A \cap B)}{\text{Area}(A \cup B)} = \frac{\max(0, \min(x_{2a}, x_{2b}) - \max(x_{1a}, x_{1b})) \times \max(0, \min(y_{2a}, y_{2b}) - \max(y_{1a}, y_{1b}))}{\text{Area}(A) + \text{Area}(B) - \text{Area}(A \cap B)}$$

**Acceptance Thresholds**:
- **Pixel-Perfect UI / Focus Ring / Spotlight**: $\text{IoU} \ge 0.95$, Center Offset $\|\Delta \mathbf{C}\|_2 \le 1.0\text{ px}$.
- **Dynamic HUD / World-to-UI Marker**: $\text{IoU} \ge 0.85$, Center Offset $\|\Delta \mathbf{C}\|_2 \le 2.0\text{ px}$.
- **Hard Stop**: Any $\text{IoU} < 0.70$ is a FAIL that requires mathematical recalculation, not manual pixel nudging.

## Kinematic Closed-Form Predictive Lead Interception

For turrets, homing projectiles, aim indicators, or lasers engaging moving entities:
- Shooter position: $\mathbf{p}_s$
- Target position: $\mathbf{p}_t$, velocity $\mathbf{v}_t$
- Projectile speed: $v_p > 0$
- Relative position: $\mathbf{r} = \mathbf{p}_t - \mathbf{p}_s$

Intercept occurs when projectile travels distance to target in time $t$:
$$\|\mathbf{r} + \mathbf{v}_t t\|^2 = (v_p t)^2$$

Solve the 2nd-order quadratic equation $A t^2 + B t + C = 0$:
$$A = \|\mathbf{v}_t\|^2 - v_p^2$$
$$B = 2 (\mathbf{r} \cdot \mathbf{v}_t)$$
$$C = \|\mathbf{r}\|^2$$
$$\Delta = B^2 - 4AC$$

**Analytical Resolution**:
1. If $\Delta < 0$ or no positive roots exist ($t \le 0$): Target cannot be intercepted directly (projectile too slow or target fleeing faster than $v_p$).
   **Closest Point of Approach (CPA) Fallback**:
   Compute relative velocity $\mathbf{v}_{\text{rel}} = \mathbf{v}_t$ (assuming stationary shooter). Time to closest approach:
   $$t_{\text{cpa}} = \max\left(0, -\frac{\mathbf{r} \cdot \mathbf{v}_{\text{rel}}}{\|\mathbf{v}_{\text{rel}}\|^2}\right)$$
   Aim at closest approach position $\mathbf{p}_{\text{cpa}} = \mathbf{p}_t + \mathbf{v}_t t_{\text{cpa}}$ to minimize miss distance.
2. If $|A| < 10^{-6}$: Linear case ($v_p = \|\mathbf{v}_t\|$), $t = -C / B$ (valid if $t > 0$).
3. If $\Delta \ge 0$:
   $$t_1 = \frac{-B - \sqrt{\Delta}}{2A}, \quad t_2 = \frac{-B + \sqrt{\Delta}}{2A}$$
   Choose the smallest positive real root: $t^* = \min(\{t \in \{t_1, t_2\} \mid t > 0\})$.
4. Exact Intercept Point: $\mathbf{p}_{\text{hit}} = \mathbf{p}_t + \mathbf{v}_t t^*$
5. Unit Firing Vector: $\hat{\mathbf{u}} = \frac{\mathbf{p}_{\text{hit}} - \mathbf{p}_s}{v_p t^*}$

## Maneuvering Targets & True Proportional Navigation (TPN)

When targets accelerate ($\mathbf{a}_t \neq \mathbf{0}$) or perform evasive maneuvers, constant-velocity quadratic intercept fails. Apply **True Proportional Navigation (TPN)** guidance (Zarchan, *Tactical and Strategic Missile Guidance*, AIAA):

$$\mathbf{a}_{\text{cmd}} = N \cdot V_c \cdot \boldsymbol{\omega}_{\text{LOS}}$$

Where:
- $N \in [3, 5]$: Navigation constant (ratio of missile acceleration to LOS rotation).
- Closing Velocity: $V_c = -\frac{d R}{dt} = -\frac{\mathbf{r} \cdot \mathbf{v}_{\text{rel}}}{\|\mathbf{r}\|}$.
- Line-of-Sight Angular Rate: $\boldsymbol{\omega}_{\text{LOS}} = \frac{\mathbf{r} \times \mathbf{v}_{\text{rel}}}{\|\mathbf{r}\|^2}$.
- **2D Planar TPN Steering Vector**: In 2D XY space with $\mathbf{r} = (r_x, r_y)$, $\dot{\lambda} = \omega_{\text{LOS}} = \frac{r_x v_{\text{rel}, y} - r_y v_{\text{rel}, x}}{\|\mathbf{r}\|^2}$:
  $$\mathbf{a}_{\text{cmd}} = N \cdot V_c \cdot \dot{\lambda} \left(-\frac{r_y}{\|\mathbf{r}\|}, \; \frac{r_x}{\|\mathbf{r}\|}\right)$$
  Retain the algebraic sign of $\dot{\lambda}$: positive $\dot{\lambda}$ steers counterclockwise (left) and negative $\dot{\lambda}$ steers clockwise (right). Never strip the sign with absolute value, which would invert control feedback for clockwise line-of-sight rotations and cause divergent steering.
- $\mathbf{a}_{\text{cmd}}$ drives $\boldsymbol{\omega}_{\text{LOS}} \to \mathbf{0}$, guaranteeing collision course even against accelerating targets.

## Ballistic Trajectories Under Gravity

To hit target at horizontal distance $x$ and vertical elevation $y$ under downward gravity $g > 0$ with muzzle velocity $v_0$ in vacuum:

$$\tan \theta = \frac{v_0^2 \pm \sqrt{v_0^4 - g(g x^2 + 2 y v_0^2)}}{g x}$$

- **Direct / Low Arc**: Choose $(-)$ root for shortest flight time.
- **Mortar / High Arc**: Choose $(+)$ root to lob over obstacles.
- **Range Limit**: If $v_0^4 - g(g x^2 + 2 y v_0^2) < 0$, target is mathematically out of reach. Maximum flat ground range: $R_{\max} = \frac{v_0^2}{g}$ at $\theta = 45^\circ$.

## Ballistic Trajectories With Aerodynamic Linear Drag (Unity Rigidbody Damping)

In Unity, `Rigidbody.linearDamping` (or legacy `drag`) introduces Stokes drag force $\mathbf{F}_d = -m k \mathbf{v}$ where $k = \frac{\text{damping}}{\text{mass}}$:

$$\frac{d\mathbf{v}}{dt} = \mathbf{g} - k \mathbf{v}$$

Analytical closed-form trajectory:
$$\mathbf{v}(t) = \frac{\mathbf{g}}{k} + \left(\mathbf{v}_0 - \frac{\mathbf{g}}{k}\right) e^{-k t}$$
$$\mathbf{x}(t) = \mathbf{x}_0 + \frac{\mathbf{g}}{k} t + \frac{1}{k}\left(\mathbf{v}_0 - \frac{\mathbf{g}}{k}\right)(1 - e^{-k t})$$

**Horizontal Range Asymptote (Finite Range Limit)**:
As $t \to \infty$, horizontal displacement approaches:
$$x_{\infty} = x_0 + \frac{v_{0x}}{k}$$
**The Drag Miss Trap**: If target horizontal distance $x_{\text{target}} \ge \frac{v_0}{k}$, the projectile will **never reach the target** regardless of launch angle or simulation time. Detect this condition before firing.

## Continuous Collision Detection & Tunneling Bound

Fast-moving bullets or colliders tunnel through geometry when velocity step exceeds minimum thickness:
$$\|\mathbf{v}\| \cdot \Delta t > D_{\min}$$

Where $D_{\min}$ is the target collider thickness. When this inequality holds, discrete triggers/raycasts miss completely.
**Fix**: Use continuous sweep volume (e.g. `Physics2D.CircleCast` or `Physics.Raycast` over the displacement segment $[\mathbf{p}(t), \mathbf{p}(t) + \mathbf{v}\Delta t]$) rather than discrete point checking.

## Rotational Kinematics & Quaternion Antipodal Slerp (Anti-Flip Guarantee)

Quaternions $\mathbf{q}$ and $-\mathbf{q}$ represent the identical 3D orientation (double cover of $SO(3)$).
Naive interpolation without antipodal checking causes violent $360^\circ$ spins (the "long way"):

$$\cos \Omega = \mathbf{q}_1 \cdot \mathbf{q}_2 = w_1 w_2 + x_1 x_2 + y_1 y_2 + z_1 z_2$$

1. **Antipodal Inversion**: If $\cos \Omega < 0$:
   $$\mathbf{q}_2 \gets -\mathbf{q}_2, \quad \cos \Omega \gets -\cos \Omega$$
2. **Small-Angle Nlerp Fallback**: If $\cos \Omega > 0.9995$ (nearly identical angles), $\sin \Omega \approx 0$ causes division by zero in Slerp. Fallback to Normalized Linear Interpolation:
   $$\text{Nlerp}(\mathbf{q}_1, \mathbf{q}_2, t) = \frac{(1 - t)\mathbf{q}_1 + t \mathbf{q}_2}{\|(1 - t)\mathbf{q}_1 + t \mathbf{q}_2\|}$$
3. **Spherical Linear Interpolation (Slerp)** (Shoemake, ACM SIGGRAPH 1985):
   $$\Omega = \arccos(\cos \Omega)$$
   $$\text{Slerp}(\mathbf{q}_1, \mathbf{q}_2, t) = \frac{\sin((1 - t)\Omega)}{\sin \Omega} \mathbf{q}_1 + \frac{\sin(t\Omega)}{\sin \Omega} \mathbf{q}_2$$

## Symplectic Euler vs Explicit Euler Numerical Energy Conservation

Unity's PhysX engine integrates physics using **Symplectic (Semi-Implicit) Euler**, updating velocity before position:
$$\mathbf{v}_{t+\Delta t} = \mathbf{v}_t + \mathbf{a}_t \Delta t$$
$$\mathbf{x}_{t+\Delta t} = \mathbf{x}_t + \mathbf{v}_{t+\Delta t} \Delta t$$

**The Explicit Euler Explosion**: If custom script physics updates position using old velocity ($\mathbf{x}_{t+\Delta t} = \mathbf{x}_t + \mathbf{v}_t \Delta t$), the system artificially gains kinetic energy at each step:
$$E_{n+1} - E_n \approx \frac{1}{2} k \Delta t^2 v_n^2 > 0$$
This causes spring-mass dampers, pendulums, and celestial orbits to spiral outward and explode. Always use Symplectic Euler in `FixedUpdate`.

## Second-Order Dynamic Systems (Harmonic Motion & Spring Juice)

General 2nd-order dynamic smoothing for camera tracking, UI springs, and procedural animation:
$$\ddot{x} + 2\zeta \omega_n \dot{x} + \omega_n^2 (x - x_{\text{target}}) = 0$$

- **Critically Damped ($\zeta = 1.0$)**: Fastest convergence without overshoot ($\omega_n \approx 2 / \text{smoothTime}$):
  $$\text{temp} = (\dot{x} + \omega_n (x - x_{\text{target}})) \Delta t$$
  $$x_{t+\Delta t} = x_{\text{target}} + (x - x_{\text{target}} + \text{temp}) e^{-\omega_n \Delta t}$$
  $$\dot{x}_{t+\Delta t} = (\dot{x} - \omega_n \text{temp}) e^{-\omega_n \Delta t}$$
- **Underdamped ($\zeta \in (0, 1.0)$)**: Natural bouncy oscillation for juicy UI pops and recoil:
  $$\omega_d = \omega_n \sqrt{1 - \zeta^2}$$
  $$x(t) = x_{\text{target}} + e^{-\zeta \omega_n t} \left( c_1 \cos(\omega_d t) + c_2 \sin(\omega_d t) \right)$$
- **Overdamped ($\zeta > 1.0$)**: Heavy, sluggish settling without oscillation.

## Unity 2D Platformer Parabolic Jump Kinematics

In 2D platformers (e.g. Mario, Celeste, Hollow Knight), tuning jump height and gravity via empirical guessing leads to floaty, unresponsive, or inconsistent platforming.
Given designer-specified parameters:
- Desired Jump Height: $h > 0$
- Desired Time to Apex: $t_{\text{apex}} > 0$

**Closed-Form Kinematic Equations**:
$$g = \frac{2h}{t_{\text{apex}}^2} \quad (\text{downward gravity acceleration})$$
$$v_{y0} = g \cdot t_{\text{apex}} = \frac{2h}{t_{\text{apex}}} \quad (\text{initial upward jump velocity})$$
- Exact platformer jump kinematic relations: `g = 2h / t_apex^2` and `v_y0 = 2h / t_apex`.

**Kinematic Trajectory & Landing Invariants**:
- Vertical position: $y(t) = v_{y0} t - \frac{1}{2} g t^2$.
- At apex ($t = t_{\text{apex}}$): $y(t_{\text{apex}}) = h$ exactly, and vertical velocity $v_y(t_{\text{apex}}) = 0$.
- Total air time on flat ground: $T_{\text{air}} = 2 t_{\text{apex}}$, with landing at $y(T_{\text{air}}) = 0$.
- Horizontal jump reach at constant speed $v_x$: $X_{\text{reach}} = 2 v_x t_{\text{apex}}$.
- Time to reach intermediate platform at height $h_{\text{plat}} < h$:
  $$t_{\text{reach}} = \frac{v_{y0} - \sqrt{v_{y0}^2 - 2 g h_{\text{plat}}}}{g}$$
- **Variable Jump Cutoff**: When jump button is released before apex, apply low-jump gravity multiplier $g_{\text{fall}} = \gamma \cdot g$ (where $\gamma \approx 2.0$ to $3.0$) or cut upward velocity $v_y \gets v_y \cdot 0.5$ to ensure snappy control.

## Box2D & Rigidbody2D Linear and Angular Drag Damping Dynamics

Unity's 2D physics engine is built on Box2D (Erin Catto). Unlike continuous Stokes integration, Box2D uses discrete numerical velocity damping integrated via **Symplectic (Semi-Implicit) Euler** per physics step (velocity is damped before updating position):

$$v_{t+\Delta t} = v_t \times \max(0, \; 1 - \Delta t \cdot d_{\text{linear}})$$
$$\omega_{t+\Delta t} = \omega_t \times \max(0, \; 1 - \Delta t \cdot d_{\text{angular}})$$
$$x_{t+\Delta t} = x_t + v_{t+\Delta t} \Delta t$$

Where $d_{\text{linear}}$ is `Rigidbody2D.linearDrag` (or `drag`) and $d_{\text{angular}}$ is `Rigidbody2D.angularDrag`.

**Discrete Geometric Decay & Symplectic Stopping Distance**:
Over $N$ steps, velocity decays as:
$$v_N = v_0 (1 - \Delta t \cdot d_{\text{linear}})^N$$
Under Symplectic Euler integration, the total discrete stopping distance from initial speed $v_0$ under pure drag dissipation:
$$S_{\text{stop, symplectic}} = \sum_{k=1}^{\infty} v_k \Delta t = v_0 (1 - \Delta t \cdot d_{\text{linear}}) \Delta t \frac{1}{\Delta t \cdot d_{\text{linear}}} = \frac{v_0 (1 - \Delta t \cdot d_{\text{linear}})}{d_{\text{linear}}} = \frac{v_0}{d_{\text{linear}}} - v_0 \Delta t$$
(Note: Continuous Stokes limit as $\Delta t \to 0$ converges to $\frac{v_0}{d_{\text{linear}}}$.)

**The 2D Drag Range Barrier**:
If a target is at distance $D > \frac{v_0}{d_{\text{linear}}}$, a projectile or sliding puck with zero sustained thrust will **mathematically never reach the target**, stopping asymptotically at $S_{\text{stop}}$. Verify that required engagement range satisfies $D < \frac{v_0}{d_{\text{linear}}}$.

## 2D Continuous Collision Detection (CCD) & Raycast2D Tunneling Bound

Fast-moving 2D entities (bullets, dashing characters, fast falling objects) tunnel through thin 2D tile colliders or box colliders when the displacement vector over a single fixed timestep $\Delta t$ exceeds the collider thickness $T_{\text{col}}$:

$$\|\mathbf{v}\| \cdot \Delta t > T_{\text{col}}$$

When this condition holds, discrete overlap tests at $t$ and $t+\Delta t$ both report no overlap, completely missing the wall.

**Continuous Swept Collision Resolution**:
1. Check tunneling bound: If $\|\mathbf{v}\|\Delta t > T_{\text{col}}$, enforce continuous sweep.
2. Sweep ray or circle along displacement segment $\mathbf{p}(t)$ to $\mathbf{p}(t) + \mathbf{v}\Delta t$:
   $$t_{\text{hit}} = \frac{\mathbf{x}_{\text{obstacle}} - \mathbf{p}(t)}{\mathbf{v} \Delta t}$$
3. If $0 \le t_{\text{hit}} \le 1$, collision occurs at $t_{\text{impact}} = t_{\text{hit}} \cdot \Delta t \le \Delta t$.
4. Resolve impact at $\mathbf{p}_{\text{impact}} = \mathbf{p}(t) + \mathbf{v} \cdot (t_{\text{hit}} \Delta t)$ and reflect velocity or zero normal component:
   $$\mathbf{v}_{\text{post}} = \mathbf{v} - (1 + e)(\mathbf{v} \cdot \hat{\mathbf{n}}) \hat{\mathbf{n}}$$

## 2D Separating Axis Theorem (SAT) Minimum Translation Vector (MTV)

For oriented 2D bounding boxes (OBB) or convex polygon colliders, collision detection and penetration resolution follow the Separating Axis Theorem:
Two convex 2D shapes $A$ and $B$ are separated if and only if there exists a projection axis $\hat{\mathbf{u}}$ upon which their projected intervals $[a_{\min}, a_{\max}]$ and $[b_{\min}, b_{\max}]$ do not overlap.

**Penetration Depth & Minimum Translation Vector (MTV)**:
For each edge normal axis $\hat{\mathbf{n}}_i$ of shapes $A$ and $B$:
$$\text{overlap}_i = \min(a_{\max, i}, b_{\max, i}) - \max(a_{\min, i}, b_{\min, i})$$
- If any $\text{overlap}_i \le 0$, shapes do not collide (separating axis found).
- If all $\text{overlap}_i > 0$, shapes intersect. The minimum penetration axis is:
  $$\hat{\mathbf{n}}_{\text{mtv}} = \arg\min_i (\text{overlap}_i), \quad \delta_{\min} = \min_i (\text{overlap}_i)$$
- Directional alignment: Ensure $\hat{\mathbf{n}}_{\text{mtv}}$ points from shape $A$ toward shape $B$:
  $$\text{if } (\mathbf{C}_B - \mathbf{C}_A) \cdot \hat{\mathbf{n}}_{\text{mtv}} < 0 \implies \hat{\mathbf{n}}_{\text{mtv}} \gets -\hat{\mathbf{n}}_{\text{mtv}}$$
  $$\mathbf{MTV} = \delta_{\min} \cdot \hat{\mathbf{n}}_{\text{mtv}}$$

Displacing dynamic body $B$ by $\mathbf{MTV}$ resolves the 2D penetration along the exact minimum translation vector with minimal kinetic energy loss and eliminates corner snagging on tilemap seams.


