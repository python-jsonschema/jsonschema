# Contributing to the Suite

All contributors to the test suite should familiarize themselves with this document.

Both pull requests *and* reviews are welcome from any and all, regardless of their "formal" relationship (or lack thereof) with the JSON Schema organization.

## Commit Access

Any existing members with commit access to the repository may nominate new members to get access, or a contributor may request access for themselves.
Access generally should be granted liberally to anyone who has shown positive contributions to the repository or organization.
All who are active in other parts of the JSON Schema organization should get access to this repository as well.
Access for a former contributor may be removed after long periods of inactivity.

## Reviewing a Pull Request

Pull requests may (and often should) be reviewed for approval by a single reviewer whose job it is to confirm the change is specified, correct, minimal and follows general style in the repository.
A reviewer who does not feel comfortable signing off on the correctness of a change is free to comment without explicit approval.
Other contributors are also encouraged to comment on pull requests whenever they have feedback, even if another contributor has submitted review comments.
A submitter may also choose to request additional feedback if they feel the change is particularly technical or complex, or requires expertise in a particular area of the specification.
If additional reviewers have participated in a pull request, the submitter should not rely on a single reviewer's approval without some form of confirmation that all participating reviewers are satisfied.
On the other hand, whenever possible, reviewers who have minor comments should explicitly mention that they are OK with the PR being merged after or potentially *without* addressing them.

When submitting a change, explicitly soliciting a specific reviewer explicitly is currently not needed, as the entire review team is generally pinged for pull requests.
Nevertheless, submitters may choose to do so if they want specific review from an individual, or if a pull request is sitting without review for a period of time.
For the latter scenario, leaving a comment on the pull request or in Slack is also reasonable.

Confirming that a pull request runs successfully on an implementation is *not* generally sufficient to merge, though it is helpful evidence, and highly encouraged.
Proposed changes should be confirmed by reading the specification and ensuring the behavior is specified and correct.
Submitters are encouraged to link to the specification whenever doing so will be helpful to a reviewer.

A reviewer may indicate that the proposed changes are too large for them to review.
In such cases the submitter may wait for another reviewer who is comfortable reviewing the changes, but is generally strongly encouraged to split up the changes into multiple smaller ones.

Reviewing pull requests is an extremely valuable contribution!
New reviewers are highly encouraged to attempt to review pull requests even if they do not have experience doing so, and to themselves expect feedback from the submitter or from other reviewers on improving the quality of their reviews.
In such cases the submitter should use their judgement to decide whether the new contributor's review is sufficient for merging, or whether they should wait for further feedback.

## Merging Changes

Approval of a change may be given using the GitHub UI or via a comment reply.
Once it has been given, the pull request may be merged at any point.

To merge a pull request, *either* the submitter or reviewer must have commit access to the repo (though this is also partially simply because that party's access is needed to merge).

*Either* the submitter or reviewer may be the one to do the actual merge (whether via hitting the merge button or externally to the GitHub UI).
If the submitter wishes to make final changes after a review they should attempt to say so (and thereby take responsibility for merging themselves).
Contributors *should not* leave pull requests stagnant whenever possible, and particularly after they have been reviewed and approved.

Changes should not be merged while continuous integration is failing.
Failures typically are not spurious and indicate issues with the changes.
In the event the change is indeed correct and CI is flaky or itself incorrect, effort should be made by the submitter, reviewer, or a solicited other contributor to fix the CI before the change is made.
Improvements to CI itself are very valuable as well, and reviewers who find repeated issues with proposed changes are highly encouraged to improve CI for any changes which may be automatically detected.

Changes should be merged *as-is* and not squashed into single commits.
Submitters are free to structure their commits as they wish throughout the review process, or in some cases to restructure the commits after a review is finished and they are merging the branch, but are not required to do so, and reviewers should not do so on behalf of the submitter without being requested to do so.

Contributors with commit access may choose to merge pull requests (or commit directly) to the repository for trivial changes.
The definition of "trivial" is intentionally slightly ambiguous, and intended to be followed by good-faith contributors.
An example of a trivial change is fixing a typo in the README, or bumping a version of a dependency used by the continuous integration suite.
If another contributor takes issue with a change merged in this fashion, simply commenting politely that they have concerns about the change (either in an issue or directly) is the right remedy.

## Writing Good Tests

Be familiar with the test structure and assumptions documented in the [README](README.md).

Test cases should include both valid and invalid instances which exercise the test case schema whenever possible.
Exceptions include schemas where only one result is ever possible (such as the `false` schema, or ones using keywords which only produce annotations).

Schemas should be *minimal*, by which we mean that they should contain only those keywords which are being tested by the specific test case, and should not contain complex values when simpler ones would do.
The same applies to instances -- prefer simpler instances to more complex ones, and when testing string instances, consider using ones which are self-descriptive whenever it aids readability.

Comments can and should be used to explain tests which are unclear or complex.
The `comment` field is present both for test cases and individual tests for this purpose.
Links to the relevant specification sections are also encouraged, though they can be tedious to maintain from one version to the next.

When adding test cases, they should be added to all past (and future) versions of the specification which they apply to, potentially with minor modifications (e.g. changing `$id` to `id` or accounting for `$ref` not allowing siblings on older drafts).

Changing the schema used in a particular test case should be done with extra caution, though it is not formally discouraged if the change simplifies the schema.
Contributors should not generally append *additional* behavior to existing test case schemas, unless doing so has specific justification.
Instead, new cases should be added, as it can often be subtle to predict which precise parts of a test case are unique.
Adding additional *tests* however (instances) is of course safe and encouraged if gaps are found.

Tests which are *incorrect* (against the specification) should be prioritized for fixing or removal whenever possible, as their continued presence in the suite can create confusion for downstream users of the suite.

## Proposing Changes to the Policy

This policy itself is of course changeable, and changes to it may be proposed in a discussion.
