import time
import sys
import git
import webbrowser

def remover_branch(gitcommand, branch):
    """ Função para remover branchs """
    branchs = gitcommand.execute("git branch --all --list *{}*".format(branch))
    if not branchs:
        return
    else:
        branchs = branchs.split("\n")
    for item in branchs:
        if "remotes" in item:
            gitcommand.execute("git push -d origin {}".format(branch))
        else:
            gitcommand.execute("git branch -D {}".format(branch))

def cherry_pick(gitcommand, commit):
    """ Função para efetuar o cherry-pick de determinado commit """
    try:
        gitcommand.execute("git cherry-pick -n --strategy=recursive -X theirs {}".format(commit))
    except:
        # Remove os arquivos alterados que foram removidos da branch atual
        # e deram conflito no cherry-pick
        files = gitcommand.execute("git diff --name-only --diff-filter=U").split("\n")
        for file in files:
            gitcommand.execute("git rm -f {}".format(file))

print("\n GERACAO DE CODE REVIEW INICIADO ")
print("-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-\n")

start_time = time.time()

story = sys.argv[1]
branch_base = sys.argv[2]
branch_review_base = "CR_BASE_{}".format(story)
branch_review_diff = "CR_DIFF_{}".format(story)
gitcommand = git.Git("C:/Projetos/mitsui")

print(">> Atualizando branches ...")
gitcommand.execute("git pull --all")
print("OK - Branches atualizadas.\n")

print(">> Acessando branch {} ...".format(branch_base))
gitcommand.execute("git checkout {}".format(branch_base))
print("OK - Branch atual {}.\n".format(branch_base))

remover_branch(gitcommand, branch_review_base)
remover_branch(gitcommand, branch_review_diff)

print(">> Listando commits da estoria {} ...".format(story))
commits = gitcommand.execute("git log --pretty=\"format:%h\" --grep=\"{}\"".format(story)).split("\n")
first_commit = commits[-1]
commits = list(reversed(commits))

print(">> INFORMACOES DE CODE REVIEW")
print(" - Estoria                 : {}".format(story))
print(" - Branch Code Review Base : {}".format(branch_review_base))
print(" - Branch Code Review Diff : {}".format(branch_review_diff))
print(" - Lista de Commits        : {}\n".format(" ".join(commits)))

try:
    print(">> Criando Branch {} ...".format(branch_review_base))
    gitcommand.execute("git checkout {}~1".format(first_commit))
    gitcommand.execute("git checkout -b {}".format(branch_review_base))
    gitcommand.execute("git push origin {}".format(branch_review_base))
    print("OK - Branch {} criada.\n".format(branch_review_base))
except Exception as e:
    print("ERRO - Ocorreu um erro ao gerar a branch {}. {}\n".format(branch_review_base, str(e)))
    print(">> Efetuando o rollback ...")
    gitcommand.execute("git reset --hard")
    gitcommand.execute("git checkout {}".format(branch_base))
    remover_branch(gitcommand, branch_review_base)
    print("OK - Rollback efetuado.")
    exit(1)

try:
    print(">> Criando Branch {} ...".format(branch_review_diff))
    gitcommand.execute("git checkout {}~1".format(first_commit))
    gitcommand.execute("git checkout -b {}".format(branch_review_diff))
    for commit in commits:
        cherry_pick(gitcommand, commit)
    gitcommand.execute("git commit -m \"[{}]: Criação de branch de Code Review\"".format(story))
    gitcommand.execute("git push origin {}".format(branch_review_diff))
    print("OK - Branch {} criada.\n".format(branch_review_diff))
except Exception as e:
    print("ERRO - Ocorreu um erro ao gerar a branch {}. {}\n".format(branch_review_diff, str(e)))
    print(">> Efetuando o rollback ...")
    gitcommand.execute("git cherry-pick --abort")
    gitcommand.execute("git reset --hard")
    gitcommand.execute("git checkout {}".format(branch_base))
    remover_branch(gitcommand, branch_review_diff)
    print("OK - Rollback efetuado.")
    exit(1)

gitcommand.execute("git checkout {}".format(branch_base))

webbrowser.open("https://bitbucket.org/ciandt_it/mitsui/branch/{}?dest={}#diff".format(branch_review_diff, branch_review_base), new=2)

hours, rem = divmod(time.time() - start_time, 3600)
minutes, seconds = divmod(rem, 60)

print(">> Geracao de Code Review Finalizado.")
print(">> Tempo de execucao: {:0>2}:{:0>2}:{:05.2f}\n".format(int(hours),int(minutes),seconds))