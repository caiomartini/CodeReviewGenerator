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
        # Adiciona os arquivos alterados que deram conflito no cherry-pick
        files = gitcommand.execute("git diff --name-only --diff-filter=U").split("\n")
        for file in files:
            if file:
                gitcommand.execute("git add {}".format(file))

def criar_branch_base(gitcommand, branch_review_base, primeiro_commit):
    try:
        print(">> Criando Branch {} ...".format(branch_review_base))
        gitcommand.execute("git checkout {}~1".format(primeiro_commit))
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

def criar_branch_diff(gitcommand, branch_review_diff, primeiro_commit, commits, tag):
    try:
        print(">> Criando Branch {} ...".format(branch_review_diff))
        gitcommand.execute("git checkout {}~1".format(primeiro_commit))
        gitcommand.execute("git checkout -b {}".format(branch_review_diff))
        for commit in commits:
            cherry_pick(gitcommand, commit)
        gitcommand.execute("git commit -n -m \"[{}]: Criação de branch de Code Review\"".format(tag))
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

def main():
    print("\n GERACAO DE CODE REVIEW INICIADO ")
    print("-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-\n")

    start_time = time.time()

    repository = sys.argv[1]
    branch_base = sys.argv[2]
    tag = sys.argv[3]
    branch_review_diff = "CR_DIFF_{}".format(tag)
    gitcommand = git.Git(repository)

    print(">> Atualizando branches ...")
    gitcommand.execute("git pull --all")
    print("OK - Branches atualizadas.\n")

    print(">> Acessando branch {} ...".format(branch_base))
    gitcommand.execute("git checkout {}".format(branch_base))
    print("OK - Branch atual {}.\n".format(branch_base))

    remover_branch(gitcommand, branch_review_diff)

    print(">> Listando commits da estoria {} ...".format(tag))
    commits = gitcommand.execute("git log --pretty=\"format:%h\" --grep=\"{}\"".format(tag)).split("\n")
    primeiro_commit = commits[-1]
    commits = list(reversed(commits))
    print("OK - Commits listados.\n")

    print(">> Informacoes de Code Review")
    print(" - Tag                : {}".format(tag))
    print(" - Branch Code Review : {}".format(branch_review_diff))
    print(" - Lista de Commits   : {}\n".format(" ".join(commits)))

    criar_branch_diff(gitcommand, branch_review_diff, primeiro_commit, commits, tag)

    ultimo_commit = gitcommand.execute("git rev-parse HEAD")

    gitcommand.execute("git checkout {}".format(branch_base))

    link = "https://bitbucket.org/ciandt_it/mitsui/commits/{}?at={}".format(ultimo_commit, branch_review_diff)
    webbrowser.open(link)

    hours, rem = divmod(time.time() - start_time, 3600)
    minutes, seconds = divmod(rem, 60)

    print(">> Geracao de Code Review finalizado.")
    print(">> Link para analise: {}".format(link))
    print(">> Tempo de execucao: {:0>2}:{:0>2}:{:05.2f}\n".format(int(hours),int(minutes),seconds))

main()