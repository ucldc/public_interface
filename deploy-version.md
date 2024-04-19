# Workflow for Development and Deployment

## Starting Development on a new Calisphere Feature:

Step 1: Make sure to do a `git fetch` to have the latest and greatest

Step 2: Create a new branch based on `ucldc:public_interface/main`, assuming `git remote -v origin` results in `origin	git@github.com:ucldc/public_interface.git`:

```git checkout -b <feature_branch> origin/main```

Step 3: When you're finished with the feature, make sure to rebase your feature branch on main before issuing a PR to make sure your branch has picked up any changes that have happened in the interim, and to make sure your feature's commits exist after any updates to `main` in a linear order:

```git rebase origin/main```

Step 4: Push your code up to origin, if you've rebased since the last time you pushed to origin, you'll probably have to force push with -f:

```git push origin <feature_branch> -f```

Step 5: Issue a PR against `ucldc:public_interface/stage` and request reviews; add milestones, labels, project board, etc

Step 6: Once the PR has been approved, use *merge* to merge it into stage with a merge commit - if the branch name is not descriptive of the feature, update the merge commit with a more descriptive title (but keep the PR # in the commit message!)

Step 7: Do any QA testing on calisphere-test and calisphere-stage

You could at this point merge many different feature branches into the stage branch, or continue to iterate on existing feature branches in response to QA testing, etc. 

Once calisphere-test and calisphere-stage are looking good...

Step 8: Create a PR from `ucldc:public_interface/stage` branch to `ucldc:public_interface/main` branch

Step 9: *Merge* the PR into main (in order to keep the same commit hashes in main's history as are used in the application version). In the future, this will trigger a build and deploy to -test and -stage. 

Step 10: [Future] Do a quick sanity check on -test and -stage that all looks good

Step 11: Deploy whatever app version is on -test and -stage to -prod

## Apply a hotfix to Calisphere Production when a QA Candidate is currently in place on calisphere-test and calisphere-stage

Step 1: Make sure to do a `git fetch` to have the latest and greatest

Step 2: Create a new branch based on `ucldc:public_interface/main`, assuming `git remote -v origin` results in `origin	git@github.com:ucldc/public_interface.git`:

```git checkout -b <fix_branch> origin/main```

Step 3: Make the fixes and push to origin
    `git push origin <fix_branch>`

Step 4: Issue a PR from `fix_branch` to `ucldc:public_interface/main`

Step 5: Optional code review, once finished, *merge* into main, which [TODO] will trigger a build and deploy to calisphere-stage and calisphere-test. 
> Note: this will result in a "roll back" of the QA candidate, but will allow us to test the fixes.

Step 6: Once fixes look good, deploy app version to production and verify we are done with hotfix.

Step 7: To update the QA candidate and put it back in place, rebase `ucldc:public_interface/stage` on the updated `ucldc:public_interface/main` and force push to stage:

```
git fetch
git checkout -b stage origin/stage
git rebase origin/main
git push origin stage -f
git checkout main
git branch -D stage
```

This will trigger a new build and deploy to -test and -stage of a new QA candidate with the fix in place. 
