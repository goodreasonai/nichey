(self.webpackChunk_N_E=self.webpackChunk_N_E||[]).push([[38],{1205:(e,t,r)=>{(window.__NEXT_P=window.__NEXT_P||[]).push(["/article",function(){return r(9648)}])},9648:(e,t,r)=>{"use strict";r.r(t),r.d(t,{default:()=>w});var i=r(4848),n=r(6540),l=r(9627),a=r(4804),c=r(7833),o=r.n(c);function s(e){let{children:t}=e;return(0,i.jsx)("div",{className:o().article,children:(0,i.jsx)(l.o,{remarkPlugins:[a.A],children:t?t.replace(/\[\[([^\]|]+)\|?([^\]]*)\]\]/g,(e,t,r)=>{let i=t.trim().replace(/\s+/g,"-").toLowerCase(),n=r.trim()||t.trim();return"[".concat(n,"](/article?e=").concat(i,")")}):""})})}var d=r(3368),u=r.n(d),h=r(6715),f=r(6080);function w(e){var t;let{}=e,r=null===(t=(0,h.useRouter)().query)||void 0===t?void 0:t.e,[l,a]=(0,n.useState)(),[c,o]=(0,n.useState)(void 0),{setPath:d}=(0,f.ok)();return(0,n.useEffect)(()=>l?(d([{href:{pathname:"/articles"},title:"Articles"},{href:{pathname:"/article",query:{e:l.slug}},title:l.title}]),()=>{d([])}):(d([{href:{pathname:"/articles"},title:"Articles"}]),()=>{d([])}),[l]),(0,n.useEffect)(()=>{async function e(){try{let e="".concat("","/api/page?slug=").concat(r),t=await fetch(e,{method:"GET"});if(!t.ok)throw Error("Response was not ok");let i=await t.json();a(i.entity),o(!0)}catch(e){console.log(e),o(!1)}}r&&e()},[r]),(0,i.jsxs)("div",{children:[(0,i.jsx)(u(),{children:(0,i.jsx)("title",{children:null==l?void 0:l.title})}),!1===c?(0,i.jsx)("div",{children:"Could not find page for '".concat(r,"'")}):(null==l?void 0:l.markdown)?(0,i.jsx)(s,{children:null==l?void 0:l.markdown}):(0,i.jsx)("div",{children:"Page for ".concat(null==l?void 0:l.title," is not yet written.")})]})}},7833:e=>{e.exports={article:"MarkdownViewer_article__CXqGO",editorArticle:"MarkdownViewer_editorArticle__Qa97H"}}},e=>{var t=t=>e(e.s=t);e.O(0,[9,636,593,792],()=>t(1205)),_N_E=e.O()}]);