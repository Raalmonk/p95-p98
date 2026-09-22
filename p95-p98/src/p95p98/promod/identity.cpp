#include <vector>
#include <algorithm>
#include <cstring>
struct V { int score, matches, gaps; };
static V best(V a,V b) {
 if(a.score!=b.score)return a.score>b.score?a:b;
 if(a.matches!=b.matches)return a.matches>b.matches?a:b;
 return a.gaps>=b.gaps?a:b;
}
static V add(V a,int s,int m,int g) {
 if(a.score<-100000000)return a;
 return {a.score+s,a.matches+m,a.gaps-g};
}
extern "C" void identity(const char* a,const char* b,const int* matrix,int* out) {
 const int n=strlen(a),m=strlen(b); V no={-1000000000,0,0};
 std::vector<V> pm(m+1,no),px(m+1,no),py(m+1,no),cm(m+1),cx(m+1),cy(m+1);
 pm[0]={0,0,0}; for(int j=1;j<=m;j++)py[j]={-11-(j-1),0,-j};
 for(int i=1;i<=n;i++) {
  cm[0]=cy[0]=no;cx[0]={-11-(i-1),0,-i};
  for(int j=1;j<=m;j++) {
   int s=matrix[(a[i-1]-'A')*26+b[j-1]-'A'],eq=a[i-1]==b[j-1];
   cm[j]=add(best(best(pm[j-1],px[j-1]),py[j-1]),s,eq,0);
   cx[j]=best(add(pm[j],-11,0,1),add(px[j],-1,0,1));
   cy[j]=best(add(cm[j-1],-11,0,1),add(cy[j-1],-1,0,1));
  }
  pm.swap(cm);px.swap(cx);py.swap(cy);
 }
 V v=best(best(pm[m],px[m]),py[m]);out[0]=v.score;out[1]=v.matches;out[2]=-v.gaps;out[3]=std::min(n,m);
}
