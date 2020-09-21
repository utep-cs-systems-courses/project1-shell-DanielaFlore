# -*- coding: utf-8 -*-
"""
@author: Flores Daniela
Lab 1
"""
#! /usr/bin/env python3

import re, sys, os

def path(parent):
    #tries each directory in the path
    for dir in re.split(':', os.environ['PATH']): 
        program = "%s/%s" % (dir, parent[0])
        try:
            #executes process
            os.execve(program, parent, os.environ) 
        except FileNotFoundError:                  
            pass                                   
    os.write(2, ("Could not exec %s\n" % parent[0]).encode())
    sys.exit(1)                                    
#handles indirection '<' '>'
def indir(symbol, number, userInput):
    #splits user input by '<' or '>'
    input = userInput.split(symbol)
    os.close(number)
    if symbol == '>':
        sys.stdout = open(input[1].strip(), 'w')
        fd = sys.stdout.fileno()
    else:
        sys.stdin = open(input[1].strip(), 'r')
        fd = sys.stdin.fileno()
    os.set_inheritable(fd, True)
    parent = input[0].split()
    path(parent)
        
while True:
    #checks if PS1 is set
    if 'PS1' in os.environ:
        os.write(1, (os.environ['PS1']).encode())
    else:
        #default prompt
        os.write(1, ('$ ').encode())
    try:
        userInput = os.read(0,128)
    except EOFError:
        sys.exit(1)
    #empty
    if len(userInput) == 0:
        continue
    #terminate
    elif 'exit' == userInput[0]: 
        sys.exit(0)
    #change directory
    elif 'cd' == userInput[0]:
        changeDir = userInput[1]
        os.chdir(changeDir)
    else:
        print("command not found!")
        
    pid = os.fork()
    #if fork fails
    if pid < 0:
        os.write(2, ('Fork failed').encode())
        sys.exit(1)
    #fork was succesful
    elif pid == 0:
        # Piping command
        if "|" in userInput: 
            pipe = userInput.split("|")
            commands = pipe[0].split()
            # file descriptors pr, pw
            pRead, pWrite = os.pipe()  
            for f in (pRead, pWrite):
                os.set_inheritable(f, True)
            pipFork = os.fork()

            if pipFork < 0:
                os.write(2, ('Fork failed').encode())
                sys.exit(1)
            #child
            if pipFork == 0:
                os.close(1) 
                os.dup(pWrite)
                os.set_inheritable(1, True)
                for fd in (pRead, pWrite):
                    os.close(fd)
                path(commands)
            #parent
            else: 
                os.close(0)
                os.dup(pRead)
                os.set_inheritable(0, True)
                for fd in (pWrite, pRead):
                    os.close(fd)
                path(pipe[1].split())
        # redirect output
        if '>' in userInput: 
            indir('>', 1, userInput)
        # redirect input
        if '<' in userInput: 
            indir('<', 0, userInput)
        else:
            parent = userInput.split()
            if '/' in parent[0]:
                program = parent[0]
                try:
                    os.execve(program, parent, os.environ)
                except FileNotFoundError:
                    pass
            else:
                path(parent)
            

