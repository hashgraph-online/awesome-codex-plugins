# OSHWA Certification Readiness

Use this reference when preparing or auditing a KiCad project for the Open
Source Hardware Association (OSHWA) certification program.

Certification is a legal and publication workflow, not an electrical safety,
EMC, radio, or manufacturing approval. Do not describe a board as OSHWA
certified until OSHWA has accepted the application and assigned a unique ID
(UID).

## Readiness Workflow

1. Define the product and version being certified. Keep the released source,
   documentation, and BOM tied to that exact version. Treat a materially new
   version as a separate registration unless current OSHWA guidance says
   otherwise.
2. Identify everything controlled by the creator: hardware, required software
   or firmware, documentation, and branding. Clearly distinguish proprietary
   third-party parts and other excluded material.
3. Publish the preferred editable source for modification. For KiCad projects,
   include the applicable `.kicad_pro`, `.kicad_sch`, `.kicad_pcb`, custom
   `.kicad_sym` libraries, `.pretty/` footprint libraries, and project-specific
   design-rule files. Include mechanical source, FPGA/firmware source, and
   build or programming instructions when needed to reproduce the product.
   Gerbers, PDFs, and rendered images are useful release artifacts but do not
   replace editable design source.
4. Publish a BOM with references, quantities, values, footprints, and enough
   manufacturer/part-number detail to reproduce the design. Ensure third-party
   components have publicly accessible datasheets.
5. Apply compatible licenses to each creator-controlled element. Use a
   recognized open hardware license for hardware (e.g. CERN-OHL, TAPR OHL,
   Solderpad), an OSI-approved license for required software, and an open
   documentation license. Do not use NonCommercial or NoDerivatives
   restrictions for certification material.
   Record the selected license in the repository and, where practical, in the
   KiCad title block or schematic/PCB text.
6. Test every public project and documentation URL in a logged-out session.
   Confirm that a user can find the source, BOM, license, version, and build
   information without requesting access.
7. Run the normal KiCad review and fabrication gates independently. OSHWA
   readiness does not replace ERC, DRC, DFM, EMC, safety, radio, or regulatory
   checks.
8. Present a readiness report with `ready`, `gap`, or `not applicable` for each
   checklist item. Separate factual repository findings from licensing
   judgments, and recommend qualified legal advice when ownership or license
   compatibility is unclear.
9. Submit the certification application only with explicit user authorization.
   Applying includes accepting OSHWA's certification license agreement and
   making claims about public artifacts, so never do it as an implicit review
   step.
10. After OSHWA issues the UID, obtain the official mark artwork, add the UID
    where appropriate, and follow the current mark-usage guide. Never invent a
    UID or place the certification mark before approval. Re-run ERC/DRC and
    regenerate release outputs after changing the schematic, PCB, enclosure,
    or documentation.

## Readiness Report

Report at least:

- project name and exact version
- public project and source URLs
- editable source inventory and missing files
- BOM completeness and datasheet accessibility
- hardware, software, and documentation licenses
- proprietary or excluded elements and how they are identified
- reproduction/build instructions
- OSHWA application status and UID, if already issued
- certification-mark status
- unrelated engineering or regulatory checks performed and skipped
- blocking gaps and the next action for each

Do not provide legal conclusions. State what the files and current OSHWA
requirements show, identify ambiguity, and request owner or counsel review for
unclear copyright, patent, trademark, contributor, or third-party-license
rights.

## Official Sources

Verify current requirements immediately before a readiness decision or
application:

- Requirements: <https://certification.oshwa.org/requirements.html>
- Certification process: <https://certification.oshwa.org/process.html>
- Hardware licensing: <https://certification.oshwa.org/process/hardware.html>
- Software licensing: <https://certification.oshwa.org/process/software.html>
- Documentation: <https://certification.oshwa.org/process/documentation.html>
- Certification mark: <https://certification.oshwa.org/mark-usage.html>
- License agreement: <https://certification.oshwa.org/license-agreement.html>
