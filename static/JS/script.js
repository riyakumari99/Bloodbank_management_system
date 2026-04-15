function confirmDelete(){
    return confirm("Are you sure?");
}

document.getElementById("searchInput")?.addEventListener("keyup",function(){
let filter=this.value.toLowerCase();
let rows=document.querySelectorAll("#donorTable tr");

rows.forEach((row,i)=>{
if(i===0)return;
row.style.display=row.innerText.toLowerCase().includes(filter)?"":"none";
});
});