# Command Catalogue

Example command lines for every `story` command, for when you need the exact form of one. `SKILL.md` says when to run each command, and the other references hold their rules. `story --help` lists every command and `story <command> --help` its flags, and `docs/cli-reference.md` documents every flag.

<!-- command-reference -->
```shell
story reindex .
story wordcount . --write
story check .
story check . --strict
story validate .
story links .
story continuity .
story prose .
story voices .
story pacing .
story clues .
story timeline .
story grid .
story grid . --format csv
story passes .
story passes . --init
story passes . --start structure
story passes . --done structure
story names 'Mira' 'Kelvos'
story mentions character sera-voss --path .
story mentions --path .
story list chapters --where status=draft --path .
story diagram relationships
story diagram locations --out dist/locations.mmd
story diagram timeline
story diagram clues
story diagram arcs
story progress . --log
story compare . --ref draft-1
story compare . --against ../book-draft-1
story snapshot draft-1 --path .
story snapshot --list --path .
story compare . --snapshot draft-1
story snapshot --restore draft-1 --dry-run --path .
story compare . --ref beta-round-1 --anchor ch03-p12
story similarity . --against ../book-one
story similarity . --snapshot draft-1
story series .
story init 'The Last Ember' --form novel
story init 'Embers of the Vale' --follows ../the-last-ember
story import draft.md --title 'Title'
story report .
story report . --actionable
story next .
story doctor .
story doctor . --fix --dry-run
story doctor . --fix
story migrate .
story add character 'Name'
story add character 'Пётр'
story add character '李明' --id li-ming
story add matter 'Dedication'
story add research 'Tidal bore timing' --source 'Tide tables 2024' --used-in chapter-03
story add research 'Night shift on a cardiac ward' --method interview --accuracy must-be-accurate --confidence medium --risk medical
story add matter 'Acknowledgments' --placement back
story rename character old-id 'New Name'
story rename character old-id 'New Name' --prose --dry-run
story rename character petr 'Пётр Иванов'
story rename character li-ming '李明华' --id li-minghua
story move chapter chapter-04 --number 5 --dry-run
story move chapter chapter-04 --number 5
story move scene chapter-03-scene-02 --chapter chapter-05
story move scene chapter-03-scene-02 --scene 1
story split chapter-07 --at 2 --dry-run
story split chapter-07 --at 'The ferry came at noon.' --title 'The Crossing'
story merge chapter-07 chapter-08
story remove promise old-promise
story export . --out dist/manuscript.md
story build . --format markdown
story build . --format epub
story build . --format docx
story build . --format shunn
story build . --format docx --shunn
story build . --format html
story build . --format print --trim 6x9
story build . --format narration
story build . --format metadata
story build . --format twee
story build . --format ink
story knowledge sera-voss --at chapter-04
story continuity . --json
story context chapter-04 --budget 6000
story add clue 'The silver locket' --planted chapter-02 --payoff chapter-05
story synopsis --pages 1
story synopsis --pages 3 --out dist/synopsis.md
```
