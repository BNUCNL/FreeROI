********************
Developer Guidelines
********************

Development process
===================

Git Repository
--------------

The git repository is structured by a number of branches and clones (forks) at
github_.

Anyone is welcome to fork the repository on github_ (just click on "Fork"
button), and file a "Pull request" whenever he/she thinks that his changes are
ready to be included (merged) into the main repository.

.. _github: https://github.com/BNUCNL/FreeROI

Working with FreeROI source code
------------------------------------

1. If you are a first-time contributor:

   * Go to github_ and click the "fork" button to create your own copy of the 
     project.

   * Clone the project to your local computer:
     ::

       git clone https://github.com/your-username/FreeROI.git
  
   * Add upstream repository:
     ::

       git remote add upstream https://github.com/BNUCNL/FreeROI.git
  
   * Now, you have remote repositories named:

     + *upstream*, which refers to the **FreeROI** repository
    
     + *origin*, which refers to your personal fork

#. Develop your contribution:
   
   * Pull the latest changes from upstream:
     ::

       git checkout master
       git pull upstream master
  
   * Create a branch for the feature you want to work on. Since the branch name
     will appear in the merge message, use a sensible name such as 
     'add-region-grow':
     ::

       git checkout -b add-region-grow
  
   * Commit locally as you progress (git add and git commit)

#. To submit your contribution:

   * Push your changes back to your fork on GitHub:
     ::

       git push origin ad-region-grow
  
   * Go to GitHub. The new branch will show up with a Pull Request button - 
     ckick it.

Divergence between upstream master and your feature branch
----------------------------------------------------------

Do *not* ever merge the main branch into your. If GitHub indicates that the
branch of your Pull Request can no longer be merged automatically, rebase
onto master:
::

  git checkout mster
  git pull upstream master
  git checkout add-region-grow
  git rebase master

If any conflicts occur, fix the according files and continue:
::

  git add conflict-file1 conflict-file2
  git rebase --continue

However, you should only rebase your own branches and must generally not
rebase any branch which you collaborate on with someone else.

Finally, you must push your rebase branch:
::

  git push --force origin add-region-grow

Some other things you might want to do
---------------------------------------

1. Delete a branch on github
   ::

     git checkout master
     # delete branch locally
     git branch -D my-unwanted-branch
     # delete branch in github
     git push origin :my-unwanted-branch

#. Check out a remote branch
   ::

     # fetch all the remote branches for you
     git fetch
     # check out the branch you are interested in, giving you a local copy
     git checkout -b test origin/test

Commits
-------

Please prefix all commit summaries with one (or more) of the following labels.
This should help others to easily classify the commits inti meaningful
categoroes:

* *BF* : bug fix

* *RF* : refactoring

* *NF* : new feature

* *ENH* : enhancement of an existing feature/facility

* *BW* : address backward-compatibility

* *OPT* : optimization

* *BK* : breaks someing and or tests fail

* *PL* : making pylint happier

* *DOC* : for all kinds of document related commits
