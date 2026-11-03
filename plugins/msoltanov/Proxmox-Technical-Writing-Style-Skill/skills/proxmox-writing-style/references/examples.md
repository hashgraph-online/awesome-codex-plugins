# Examples

Each example shows text that breaks the rules, a correct rewrite, and the rules that apply.

The rewrites follow the Proxmox rules in `SKILL.md`. For example, they use contractions and US English.

## 1. Product Names and Abbreviations

Before:

> PVE supports ZFS, LVM and Ceph storage, e.g. for VM disks.

After:

> Proxmox VE supports ZFS, LVM, and Ceph storage, for example, for virtual machine disks.

Rules:

- Use the full product name. Do not write `PVE` in prose.
- Use the Oxford comma.
- Write `for example`, not `e.g.`.
- Write the full term when the text has not introduced `VM`.

## 2. Mood in Instructions

Before:

> You should probably restart the node after you've changed the network configuration.

After:

> Restart the node after you change the network configuration.

Rules:

- Use the imperative mood for instructions.
- Do not use `should`, `could`, or `might` in instructions.
- Remove words that add no fact, such as `probably`.

## 3. Voice in Descriptions

Before:

> We have added a new backup scheduler, which can be configured by one in the datacenter view.

After:

> The datacenter view contains the settings for the backup scheduler.

Rules:

- Use the third-person indicative mood for descriptions.
- Do not use first-person plural.
- Do not use `one` as a pronoun.
- Use active voice.

## 4. Procedures

Before:

> To add an NFS storage, go to Datacenter, then Storage, click Add and pick NFS, and then fill in the fields and press Add.

After:

> ### Add an NFS storage
>
> 1. In the web interface, select **Datacenter** > **Storage**.
> 2. Click **Add**.
> 3. Select **NFS**.
> 4. Enter the ID, the server, and the export path.
> 5. Click **Add**.

Rules:

- Give the procedure a descriptive heading.
- Use a numbered list for ordered steps.
- Make each step one clear action.
- Use parallel structure across the steps.
- Use sentence-style capitalization for a level 3 heading.

## 5. The Enter Key

Before:

> 1. Type `pveversion -v`.
> 2. Press Enter.

After:

> 1. Type `pveversion -v` and press Enter.

Rules:

- Include `Enter` in the same step that needs it.
- Do not use a comma between the two verbs of a compound predicate.

## 6. Headings

Before:

> ## configuring the firewall for a cluster
>
> #### Enabling The Firewall On A Node

After:

> ## Configuring the Firewall for a Cluster
>
> #### Enabling the firewall on a node

Rules:

- Use title-style capitalization for level 1 and level 2 headings.
- Lowercase short prepositions and articles in title-style headings.
- Use sentence-style capitalization for level 3 and lower headings.

## 7. Terms

Before:

> Plug the USB stick into the mainboard and install Proxmox.

After:

> Connect the USB flash drive to a USB port on the motherboard and install Proxmox VE.

Rules:

- Write `USB flash drive`, not `USB stick`.
- Write `motherboard`, not `mainboard`.
- Do not use `Proxmox` alone as a product name.

## 8. Guests and Containers

Before:

> Backups run for VMs and CTs, i.e. all guests, approx. every 24 hours.

After:

> Backups run about every 24 hours for all guests, that is, virtual machines and containers.

Rules:

- Write `container`, not `CT`, unless the text names a UI item.
- Write `that is`, not `i.e.`.
- Write `about`, not `approx.`.

## 9. Acronyms

Before:

> Configure HA for the virtual machine. HA needs a quorum.

After:

> Configure high availability (HA) for the virtual machine. HA needs a quorum.

Rules:

- Spell out an acronym at first use, followed by the acronym in parentheses.
- Do not introduce an acronym that appears only once.

## 10. Hyphens and Em Dashes

Before:

> `qm` is a command line tool - it manages virtual machines from the shell.

After:

> `qm` is a command-line tool—it manages virtual machines from the shell.

Rules:

- Use a hyphen in a compound modifier before a noun.
- Use an em dash without spaces around it.
