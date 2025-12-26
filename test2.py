def c3(x):
    s=''
    while x:
        s = str(x%3)+s
        x = x//3
    return s
mins = None
i=[]
for n in range(1,200):
    a = c3(n)
    if n%3==0:
        a = a+a[-2:]
    else:
        a = a + c3(n%3*5)
    r = int(a,3)
    if r>150 and (mins is None or r<mins):
        mins = r
print(mins)
