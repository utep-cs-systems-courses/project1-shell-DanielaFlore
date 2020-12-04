#! /usr/bin/env python3

import os,sys,re


def execute(args):
    #empty return
    if len(args) == 0:
        return
    #exit
    elif args[0].lower() == "exit":
        sys.exit(0)
    #change directory
    elif args[0] == "cd":
        try:
            #cd..
            if len(args) == 1:
                os.chdir("..")
            #go to given directory
            else:
                os.chdir(args[1])
        except:
            os.write(1, ("cd %s: No such file or directory" % args[1]).encode())
            pass
    #pipe
    elif "|" in args:
        pipe(args)
    else:
        rc = os.fork()
        background = True
        #&/background
        if "&" in args:
            args.remove("&")
            background = False
        if rc < 0:
            os.write(2, ("fork failed, returning %d\n" % rc).encode())
            sys.exit(1)
        elif rc == 0:
                if "/" in args[0]:
                    program = args[0]
                    try:
                        os.execve(program, args, os.environ)
                    except FileNotFoundError:
                        pass
                elif ">" in args or "<" in args:
                    redirection(args)
                else:
                    for dir in re.split(":", os.environ['PATH']): # try each directory in the path
                        program = "%s/%s" % (dir, args[0])
                        try:
                            os.execve(program, args, os.environ) # try to exec program
                        except FileNotFoundError:     #...expected
                            pass                      #...fail quietly
                #command not found
                os.write(2, ("command not found\n").encode())
                sys.exit(0)    #terminate
                
        else:
            if background:
                #wait for child
                childpid = os.wait()

def pipe(args):
    left = args[0:args.index("|")]
    right = args[args.index("|") + 1:]
    pRead, pWrite = os.pipe()
    rc = os.fork()
    if rc < 0: 
        os.write(2, ("fork failed, returning %d\n" % rc).encode())
        sys.exit(1)
    elif rc == 0:
        os.close(1)
        os.dup(pWrite)
        os.set_inheritable(1, True)
        for fd in (pRead, pWrite):
            os.close(fd)
        commands(left)
        os.write(2, ("Could not exec %s\n" % left[0]).encode())
        sys.exit(1)
    else:
        os.close(0)
        os.dup(pRead)
        os.set_inheritable(0, True)
        for fd in (pWrite, pRead):
            os.close(fd)
        if "|" in right:
            pipe(right)
        commands(right)
        os.write(2, ("Could not exec %s\n" % right[0]).encode())
        sys.exit(1)
# redirect
def redirection(args):
    #output
    if '>' in args:
        os.close(1)
        os.open(args[args.index('>')+1], os.O_CREAT | os.O_WRONLY)
        os.set_inheritable(1,True)
        args.remove(args[args.index('>') + 1])
        args.remove('>')
    #input
    else:
        os.close(0)
        os.open(args[args.index('<')+1], os.O_RDONLY);
        os.set_inheritable(0, True)
        args.remove(args[args.index('<') + 1])
        args.remove('<')
    
    for dir in re.split(":", os.environ['PATH']): # try each directory in path
        prog = "%s/%s" % (dir,args[0])
        try:
            os.execve(prog, args, os.environ) # try to exec program
        except FileNotFoundError:     #...expected
            pass     #...fail quietly
    os.write(2, ("%s: command not found\n" % args[0]).encode())
    sys.exit(0)
    
        
def commands(args):
    if "/" in args[0]:
        program = args[0]
        try:
            os.execve(program, args, os.environ)
        except FileNotFoundError:
            pass
    elif ">" in args or "<" in args:
        redirection(args)
    else:
        for dir in re.split(":", os.environ['PATH']): # try each directory in the path
            program = "%s/%s" % (dir, args[0])
            try:
                os.execve(program, args, os.environ) # try to exec program
            except FileNotFoundError:     #...expected
                pass     #...fail quietly
    os.write(2, ("%s: command not found\n" % args[0]).encode())
    sys.exit(0)

while True:
    if 'PS1' in os.environ: #if defined
        os.write(1, (os.environ['PS1']).encode())
    else: # PS1 variable set to '$'
        os.write(1, ("$ ").encode())
    args = os.read(0, 1024)
    #empty input
    if len(args) == 0:
        break
    args = args.decode().splitlines()
    #splits line into a list where each word is an item
    for arg in args:
        execute(arg.split())
