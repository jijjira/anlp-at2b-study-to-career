# How we work in this repo (6 people)

**Golden rule: each student works only inside their own folder** (`step1_data/` to `step6_app/`) and their file in `report/`. Because nobody edits the same files, merges stay painless.

| Folder | Owner |
|---|---|
| `step1_data/` | Student 1, Zheke Yi |
| `step2_dictionary/` | Student 2, Wancheng Liu |
| `step3_baseline_nlp/` | Student 3, Jirawan Pedersen |
| `step4_semantic/` | Student 4, Tao Lou |
| `step5_matching/` | Student 5, Tengxiao Nong |
| `step6_app/` | Student 6, Chongyan Tang |
| `report/` | one file per student, see its README |
| root files (`README.md`, `requirements.txt`, `.gitignore`, `data/`) | shared: message the group first, or open a pull request |

## Adding your work without Terminal (easiest)
1. Open the repo on GitHub, then open your step folder.
2. Choose **Add file, then Upload files**, drag your files in, write a short message such as `step4: add semantic model`, and commit.
3. Fill in your section of the main `README.md` (pencil icon, edit, commit).

## Adding your work with Terminal
```
git clone https://github.com/jijjira/anlp-at2b-study-to-career.git
cd anlp-at2b-study-to-career
git pull
git add step4_semantic
git commit -m "step4: add semantic model"
git push
```
Always run `git pull` before you start and before you push. Change `step4_semantic` to your own folder.

## Rules for code and notebooks
* Notebooks are committed **with outputs**, after Restart and Run All.
* The first cell of every notebook must work for anyone (group or instructor), with no personal paths. Copy the setup cell from the Step 3 notebooks.
* Extra libraries go in your own folder's `requirements.txt`, not the shared one.
* Do not commit `.venv/`, `__pycache__/`, files over 25 MB, passwords or tokens.
* Dictionary changes: Student 2 merges them and tells Students 3 to 5.

## Before 14 Oct
Use the checklist at the bottom of the main `README.md`.
