(self.webpackChunk_N_E=self.webpackChunk_N_E||[]).push([[231],{3271:(e,l,t)=>{(window.__NEXT_P=window.__NEXT_P||[]).push(["/source",function(){return t(2121)}])},8196:(e,l,t)=>{"use strict";t.d(l,{A:()=>i});let i={src:"/_next/static/media/DeleteIcon.f2407bd6.png",height:512,width:512,blurDataURL:"data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAMAAADz0U65AAAAHlBMVEUAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAC3KG9qAAAACnRSTlMBkTmeKnYVx3RNBEX1lAAAAAlwSFlzAAAOxAAADsQBlSsOGwAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAAySURBVHicLcbHEQAwCASxhSO5/4Y9DnoJcMkBsrs7gYmqGMA80+3G7GfmZVWtk5CkYAMaDQC3yzKOHwAAAABJRU5ErkJggg==",blurWidth:8,blurHeight:8}},96:(e,l,t)=>{"use strict";t.d(l,{A:()=>r});var i=t(4848);function r(e){let{value:l,onClick:t}=e;return(0,i.jsx)("button",{onClick:t,style:{padding:"5px"},children:l})}},4374:(e,l,t)=>{"use strict";t.d(l,{A:()=>o});var i=t(4848);t(6540);var r=t(9627),n=t(4804),s=t(7833),a=t.n(s);function o(e){let{children:l}=e;return(0,i.jsx)("div",{className:a().article,children:(0,i.jsx)(r.o,{remarkPlugins:[n.A],children:(e=>{if(!e)return"";let l=0,t=()=>l+=1;return e.replace(/\[\[([^\]|]+)\|?([^\]]*)\]\]/g,(e,l,i)=>{let r=l.trim().replace(/\s+/g,"-").toLowerCase(),n=i.trim()||l.trim();if("@"==n.charAt(0)){let e=t();return"[[".concat(e,"]](/source?id=").concat(n.substring(1),")")}return"[".concat(n,"](/article?e=").concat(r,")")})})(l)})})}},5697:(e,l,t)=>{"use strict";t.d(l,{A:()=>d});var i=t(4848);let r={src:"/_next/static/media/CloseIcon.8995a7c5.png"};var n=t(6540),s=t(961),a=t(4881),o=t.n(a);function d(e){let{isOpen:l,close:t,title:a,minWidth:d="500px",minHeight:c="unset",style:u,children:A}=e,h=(0,n.useRef)(null),v=(0,n.useRef)(null),x=(0,n.useRef)(null);return((0,n.useEffect)(()=>{let e=e=>{e.target===h.current&&t()};try{l?window.addEventListener("mousedown",e,{capture:!0}):window.removeEventListener("mousedown",e,{capture:!0})}catch(e){}return()=>{try{window.removeEventListener("mousedown",e,{capture:!0})}catch(e){}}},[l,t]),l)?s.createPortal((0,i.jsx)("div",{className:o().overlay,style:u,ref:h,children:(0,i.jsx)("div",{className:o().containerContainer,ref:x,style:{overflow:"hidden",transition:"all .1s linear"},children:(0,i.jsxs)("div",{className:o().container,style:{},ref:v,children:[(0,i.jsxs)("div",{className:o().header,children:[(0,i.jsx)("div",{className:o().title,children:a}),(0,i.jsx)("div",{style:{display:"flex",alignItems:"center"},onClick:()=>{t()},children:(0,i.jsx)("img",{src:r.src,style:{cursor:"pointer"},onClick:t,alt:"Close",width:17,height:17})})]}),(0,i.jsx)("div",{className:o().body,children:A})]})})}),document.body):""}},2121:(e,l,t)=>{"use strict";t.r(l),t.d(l,{default:()=>A});var i=t(4848),r=t(6540);t(4374);var n=t(3368),s=t.n(n),a=t(6715),o=t(6080),d=t(8196),c=t(5697),u=t(96);function A(e){var l;let{}=e,t=null===(l=(0,a.useRouter)().query)||void 0===l?void 0:l.id,[n,A]=(0,r.useState)(),[h,v]=(0,r.useState)(void 0),[x,p]=(0,r.useState)(!1),{setPath:f}=(0,o.ok)();async function y(){try{let e="".concat("","/api/source?id=").concat(t),l=await fetch(e,{method:"GET"});if(!l.ok)throw Error("Response was not ok");let i=await l.json();A(i.source),v(!0)}catch(e){console.log(e),v(!1)}}async function m(){p(!1);try{if(!(await fetch("".concat("","/api/delete-source"),{headers:{"Content-Type":"application/json"},body:JSON.stringify({id:t}),method:"POST"})).ok)throw Error("Could not save");y()}catch(e){console.log(e)}}(0,r.useEffect)(()=>n?(f([{href:{pathname:"/sources"},title:"Sources"},{href:{pathname:"/source",query:{id:n.id}},title:n.title}]),()=>{f([])}):(f([{href:{pathname:"/sources"},title:"Sources"}]),()=>{f([])}),[n]),(0,r.useEffect)(()=>{t&&y()},[t]);let _=[{label:"URL",value:(0,i.jsx)("a",{href:null==n?void 0:n.url,children:null==n?void 0:n.url}),hidden:!(null==n?void 0:n.url)},{label:"Search Engine",value:null==n?void 0:n.search_engine,hidden:!(null==n?void 0:n.search_engine)},{label:"Query",value:null==n?void 0:n.query,hidden:!(null==n?void 0:n.query)},{label:"Snippet",value:null==n?void 0:n.snippet,hidden:!(null==n?void 0:n.snippet)}];return(0,i.jsxs)("div",{children:[(0,i.jsx)(s(),{children:(0,i.jsx)("title",{children:null==n?void 0:n.title})}),!1===h?(0,i.jsx)("div",{children:"Could not find source with id '".concat(t,"'")}):n?(0,i.jsxs)("div",{style:{display:"flex",flexDirection:"column",gap:"1rem"},children:[(0,i.jsx)("h1",{children:n.title}),_.filter(e=>!e.hidden).map(e=>(0,i.jsxs)("div",{style:{display:"flex"},children:[(0,i.jsx)("div",{style:{flex:"1"},children:e.label}),(0,i.jsx)("div",{style:{flex:"1"},children:e.value})]}))]}):"",(0,i.jsxs)("div",{style:{position:"fixed",right:"10px",bottom:"10px",display:"flex",gap:"10px",alignItems:"center"},children:[(0,i.jsx)("div",{onClick:()=>{p(!0)},style:{backgroundColor:"var(--highlight)",border:"1px solid var(--border-color)",borderRadius:"5px",padding:"5px",cursor:"pointer",display:"flex",alignItems:"center"},children:(0,i.jsx)("img",{src:d.A.src,width:20,height:20,alt:"Delete"})}),(0,i.jsx)(c.A,{title:"Delete",isOpen:x,close:()=>p(!1),children:(0,i.jsxs)("div",{style:{display:"flex",flexDirection:"column",gap:"1rem",alignItems:"center"},children:[(0,i.jsx)("div",{children:"Are you sure you would like to delete the source ".concat(null==n?void 0:n.title,"?")}),(0,i.jsxs)("div",{style:{display:"flex",gap:"10px"},children:[(0,i.jsx)(u.A,{value:"Delete",onClick:()=>m()}),(0,i.jsx)(u.A,{value:"Cancel",onClick:()=>{p(!1)}})]})]})})]})]})}},7833:e=>{e.exports={article:"MarkdownViewer_article__CXqGO",editorArticle:"MarkdownViewer_editorArticle__Qa97H"}},4881:e=>{e.exports={overlay:"Modal_overlay__2Sh3U",fadeIn:"Modal_fadeIn__Oj_FH",container:"Modal_container__jKKR0",closeModal:"Modal_closeModal__QVqd2",header:"Modal_header__Pfr2K",title:"Modal_title__a7vfd",body:"Modal_body__KZX7m"}}},e=>{var l=l=>e(e.s=l);e.O(0,[9,636,593,792],()=>l(3271)),_N_E=e.O()}]);