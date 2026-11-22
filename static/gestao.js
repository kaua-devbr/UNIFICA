"use strict";
const state = JSON.parse(document.querySelector("#data").textContent);
const byId = id => document.getElementById(id);
const dialog = byId("modal"), body = byId("modal-body");
const types = {conta:"usuário",aluno:"aluno",administrador:"administrador",professor:"professor",
    turma:"turma",evento:"evento",nota:"registro acadêmico",comunicado:"comunicado"};
const records = {conta:state.accounts,turma:state.groups,evento:state.events,nota:state.grades,comunicado:state.notices};
const roles = ["aluno","administrador","professor"];
const pretty = value => String(value ?? "");
function el(tag,text,cls) {
    const node=document.createElement(tag);
    if(text !== undefined) node.textContent=pretty(text);
    if(cls) node.className=cls;
    return node;
}
function button(text,fn,cls) {
    const b=el("button",text,cls);
    b.type="button"; b.addEventListener("click",fn); return b;
}
function hidden(form,name,value) {
    const input=el("input"); input.type="hidden"; input.name=name; input.value=value; form.append(input);
}
function show(title) {
    byId("modal-title").textContent=title;
    body.replaceChildren();
    if(!dialog.open) dialog.showModal();
}
function message(title,text) {
    show(title); body.append(el("p",text),button("OK",()=>dialog.close()));
}
function field(grid,name,label,type,value,options={}) {
    const wrap=el("label",label,options.wide?"wide":"");
    if(type==="date" || type==="datetime-local") return calendarField(grid,name,label,value,type==="datetime-local");
    const input=el(type==="select"?"select":type==="textarea"?"textarea":"input");
    input.name=name;
    if(input.tagName==="INPUT") input.type=type;
    if(options.choices) for(const pair of options.choices){
        const [v,t]=Array.isArray(pair)?pair:[pair,pair];
        const opt=el("option",t); opt.value=v; input.append(opt);
    }
    for(const key of ["min","max","step","minLength","maxLength"]) if(options[key]!==undefined) input[key]=options[key];
    input.required=!options.optional;
    input.value=pretty(value);
    wrap.append(input); grid.append(wrap); return input;
}
function calendarField(grid,name,label,initial,withTime){
    const wrap=el("div"), value=el("input"), trigger=button("",openCalendar);
    value.type="hidden"; value.name=name; value.value=initial;
    function caption(){
        const [day,time]=value.value.split("T");
        trigger.textContent=label+" · "+day.split("-").reverse().join("/")+(time?" "+time:"");
    }
    function openCalendar(){
        const picker=el("dialog"), heading=el("strong"), days=el("div");
        days.className="picker-days";
        let [selected,time]=value.value.split("T");
        const [year,month]=selected.split("-").map(Number);
        let shown=new Date(year,month-1,1);
        const pad=n=>String(n).padStart(2,"0");
        function draw(){
            heading.textContent=shown.toLocaleDateString("pt-BR",{month:"long",year:"numeric"});
            days.replaceChildren();
            for(const day of ["Dom","Seg","Ter","Qua","Qui","Sex","Sáb"]) days.append(el("small",day));
            for(let i=0;i<shown.getDay();i++) days.append(el("span"));
            const count=new Date(shown.getFullYear(),shown.getMonth()+1,0).getDate();
            for(let n=1;n<=count;n++){
                const iso=[shown.getFullYear(),pad(shown.getMonth()+1),pad(n)].join("-");
                const b=button(n,()=>{selected=iso;draw();days.querySelector('[aria-pressed="true"]').focus()});
                b.setAttribute("aria-pressed",String(selected===iso));days.append(b);
            }
        }
        function move(n){shown.setMonth(shown.getMonth()+n);draw()}
        const nav=el("div",undefined,"controls");
        nav.append(button("Anterior",()=>move(-1)),heading,button("Próximo",()=>move(1)));
        picker.setAttribute("aria-label",label);
        picker.append(nav,days);
        let hours,minutes;
        if(withTime){
            const clock=el("div",undefined,"controls");
            function part(label,count,current){
                const container=el("label",label), select=el("select");
                for(let n=0;n<count;n++) select.add(new Option(pad(n),pad(n)));
                select.value=current;container.append(select);clock.append(container);return select;
            }
            hours=part("Hora",24,time.slice(0,2));minutes=part("Minuto",60,time.slice(3,5));
            picker.append(clock);
        }
        picker.append(button("Cancelar",()=>picker.close()),button("Confirmar",()=>{
            value.value=selected+(withTime?"T"+hours.value+":"+minutes.value:"");caption();picker.close()
        }));
        document.body.append(picker);
        picker.addEventListener("close",()=>{picker.remove();trigger.focus()},{once:true});
        draw();picker.showModal();
    }
    caption();wrap.append(value,trigger);grid.append(wrap);return value;
}
function formFor(kind,id) {
    const form=el("form"); form.method="post"; form.action="alterar/"+kind;
    hidden(form,"form_token",state.csrf); hidden(form,"pagina",state.page);
    hidden(form,"dia_atual",state.day); if(id) hidden(form,"id",id);
    body.append(form); return form;
}
function finish(form,text="Salvar alterações",danger=false) {
    const footer=el("div",undefined,"controls");
    const save=el("button",text,danger?"danger":""); save.type="submit";
    footer.append(button("Cancelar",()=>dialog.close(),"quiet"),save); form.append(footer);
}
function findRecord(kind,id) {
    return records[kind]?.find(r=>pretty(kind==="conta"?r.matricula:r.id)===pretty(id));
}
function edit(kind,id) {
    const type=roles.includes(kind)?"conta":kind;
    const row=id?findRecord(type,id):{};
    if(!row) return;
    show((id?"Editar ":"Novo cadastro · ")+types[kind]);
    const form=formFor(type,id),grid=el("div",undefined,"formgrid");form.append(grid);
    const f=(name,label,t="text",opts={},fallback="")=>field(grid,name,label,t,row[name]??fallback,opts);
    if(type==="conta"){
        if(!id){
            f("matricula","Matrícula","text",{maxLength:60});
            if(kind==="conta") f("papel","Tipo de usuário","select",{choices:roles},"aluno");
            else hidden(form,"papel",kind);
        }
        f("nome","Nome completo","text",{maxLength:150});f("email","E-mail","email",{maxLength:254});
        const group=f("turma","Turma","text",{optional:true,maxLength:80});
        const list=el("datalist");list.id="group-options";group.setAttribute("list",list.id);
        state.groups.forEach(g=>{const o=el("option");o.value=g.nome;list.append(o)});grid.append(list);
        const roleSelect=form.elements.papel;
        const subject=f("materia","Matéria lecionada","text",{maxLength:100});
        function updateRole(){
            const role=row.papel||roleSelect?.value;
            const teacher=role==="professor";
            group.parentElement.hidden=teacher;
            group.disabled=teacher;
            group.required=role==="aluno";
            subject.parentElement.hidden=!teacher;
            subject.disabled=!teacher;
            subject.required=teacher;
        }
        updateRole();roleSelect?.addEventListener("change",updateRole);
        f("ativo","Situação","select",{choices:[["1","Ativo"],["0","Inativo"]]},"1");
        if(!id) f("senha","Senha inicial","password",{minLength:8,maxLength:256});
    }else if(type==="turma"){
        f("nome","Nome da turma","text",{maxLength:80,wide:true});
    }else if(type==="evento"){
        f("titulo","Título do evento","text",{wide:true,maxLength:150});f("dia","Data","date",{},state.day);
        f("inicio","Início","time",{},"09:00");f("fim","Término","time",{},"10:00");
        f("descricao","Descrição","textarea",{optional:true,wide:true,maxLength:4000});
    }else if(type==="comunicado"){
        f("titulo","Título","text",{wide:true,maxLength:150});
        f("conteudo","Conteúdo da publicação","textarea",{wide:true,maxLength:8000});
        f("publicacao","Data e hora da publicação","datetime-local",{},state.now);
        f("categoria","Categoria","select",{choices:[["avisos","Avisos"],["prazos","Prazos e entregas"],["calendario","Calendário"]]},"avisos");
        f("status","Status","select",{choices:["Publicado","Rascunho"]},"Publicado");
    }else if(type==="nota"){
        const pupils=state.accounts.filter(a=>a.papel==="aluno").map(a=>[a.matricula,a.nome+" · "+a.matricula]);
        if(!pupils.length){message("Registrar nota","Cadastre um aluno para lançar notas e frequência.");return}
        f("matricula","Aluno","select",{choices:pupils,wide:true},pupils[0][0]);
        f("disciplina","Disciplina","text",{maxLength:100});f("periodo","Período","select",{choices:[1,2,3,4].map(n=>[n,n+"º bimestre"])},"1");
        f("nota","Nota","number",{min:0,max:10,step:0.01});f("aulas","Aulas dadas","number",{min:1,max:99999});
        f("faltas","Faltas","number",{min:0,max:99999},0);
    }
    finish(form,id?"Salvar alterações":"Salvar cadastro");
}
function remove(kind,id) {
    const row=findRecord(kind,id);if(!row)return;
    show("Confirmar exclusão");
    body.append(el("p","Deseja excluir "+(row.titulo||row.nome||row.disciplina)+"? Esta ação é permanente."));
    const form=formFor(kind,id);hidden(form,"acao","excluir");finish(form,"Excluir",true);
}
function badge(text,off=false){return el("span",text,"pill"+(off?" off":""))}
function actions(kind,id) {
    const span=el("span");
    span.append(button("Editar",()=>edit(kind,id),"quiet"),button("Excluir",()=>remove(kind,id),"danger"));return span;
}
let pageNo=1,tab="nota";
const term=id=>(byId(id)?.value||"").trim().toLocaleLowerCase("pt-BR");
const matches=(haystack,query)=>haystack.toLocaleLowerCase("pt-BR").includes(query);
function table(headers,data,cells) {
    const target=byId("results");target.replaceChildren();
    if(!data.length){target.append(el("p","Nenhum registro encontrado."));return}
    const pages=Math.ceil(data.length/6);pageNo=Math.min(pageNo,pages);
    const scroll=el("div",undefined,"scroll"),t=el("table"),head=t.createTHead().insertRow(),rows=t.createTBody();
    headers.forEach(h=>head.append(el("th",h)));
    data.slice((pageNo-1)*6,pageNo*6).forEach(r=>{
        const tr=rows.insertRow();cells(r).forEach(v=>{const td=tr.insertCell();if(v instanceof Node) td.append(v);else td.textContent=pretty(v)});
    });
    scroll.append(t);target.append(scroll);
    const pager=el("div",undefined,"pager");
    const prev=button("‹ Anterior",()=>{pageNo--;render()},"quiet"),next=button("Próxima ›",()=>{pageNo++;render()},"quiet");
    prev.disabled=pageNo<=1;next.disabled=pageNo>=pages;
    pager.append(prev,el("span",pageNo+" de "+pages),next);target.append(pager);
}
function render() {
    if(!byId("results"))return;
    const query=term("search"),page=state.page;
    if(page==="comunicados"){
        const list=state.notices.filter(r=>matches(r.titulo+" "+r.conteudo,query)&&matches(r.status,term("status")));
        table(["Título","Conteúdo","Publicação","Status","Ações"],list,r=>[r.titulo,r.conteudo,r.publicacao.slice(0,10).split("-").reverse().join("/")+" "+r.publicacao.slice(11),badge(r.status,r.status==="Rascunho"),actions("comunicado",r.id)]);
    }else if(page==="turmas"){
        table(["Turma","Alunos","Ações"],state.groups.filter(g=>matches(g.nome,query)),g=>[g.nome,state.accounts.filter(a=>a.papel==="aluno"&&a.turma===g.nome).length,actions("turma",g.id)]);
    }else if(page==="notas"){
        const list=state.grades.filter(r=>matches(r.nome+" "+r.matricula,query)&&(!term("class")||r.turma===byId("class").value)&&(!term("subject")||r.disciplina===byId("subject").value)&&(!term("period")||String(r.periodo)===term("period")));
        const total=k=>list.reduce((sum,r)=>sum+Number(r[k]),0);
        const summary=byId("summary"),fmt=n=>n.toLocaleString("pt-BR",{maximumFractionDigits:1});
        const people=new Set(list.map(r=>r.matricula));
        summary.replaceChildren(el("strong",people.size===1?list[0].nome+" · "+list[0].matricula:people.size+" aluno(s)"),el("span","Média: "+(list.length?fmt(total("nota")/list.length):"—")),el("span","Frequência: "+(total("aulas")?fmt(100*(1-total("faltas")/total("aulas")))+"%":"—")));
        const freq=tab==="freq";
        table(["Aluno","Disciplina","Bimestre",...(freq?["Aulas","Faltas"]:["Nota"]),"Ações"],list,r=>[r.nome,r.disciplina,r.periodo,...(freq?[r.aulas,r.faltas]:[fmt(Number(r.nota))]),actions("nota",r.id)]);
    }else{
        const role={inicio:"aluno",administradores:"administrador",professores:"professor"}[page];
        const list=state.accounts.filter(r=>(!role||r.papel===role)&&matches(r.nome+" "+r.matricula,query));
        table(["Nome","RA",page==="professores"?"Matéria":page==="usuarios"?"Turma / matéria":"Turma","Situação","Ações"],list,r=>[r.nome,r.matricula,(r.papel==="professor"?r.materia:r.turma)||"—",badge(r.ativo?"Ativo":"Inativo",!r.ativo),actions("conta",r.matricula)]);
    }
}
document.addEventListener("click",e=>{
    const b=e.target.closest("button");if(!b)return;
    if(b.hasAttribute("data-close"))dialog.close();
    if(b.dataset.new)edit(b.dataset.new);
    if(b.dataset.edit)edit(b.dataset.edit,b.dataset.id);
    if(b.dataset.delete)remove(b.dataset.delete,b.dataset.id);
    if(b.dataset.tab){tab=b.dataset.tab;document.querySelectorAll("[data-tab]").forEach(t=>t.setAttribute("aria-pressed",String(t===b)));render()}
    if(b.hasAttribute("data-password")){
        show("Alterar senha");
        const iframe=el("iframe");iframe.title="Alteração de senha do UNIFICA";iframe.src="/sso/senha";iframe.style.cssText="border:0;width:100%;height:min(62vh,27rem)";
        iframe.addEventListener("load",()=>{if(iframe.contentWindow.location.pathname==="/sso/login")location.assign("/sso/login")});
        body.append(iframe);
    }
});
dialog.addEventListener("click",e=>{if(e.target===dialog){const r=dialog.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)dialog.close()}});
for(const id of ["search","class","subject","period","status"])byId(id)?.addEventListener("input",()=>{pageNo=1;render()});
byId("filters")?.addEventListener("submit",e=>{e.preventDefault();pageNo=1;render()});
render();
if(state.messages.length){const [category,text]=state.messages.at(-1);message(category==="erro"?"Confira os dados":"Concluído",text)}

