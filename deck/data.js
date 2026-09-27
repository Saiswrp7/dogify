// Research-backed slide content. Every number comes from deck/research.md, which holds the sources and quotes.
const badge = (t) => `<span class="hand" style="font-size:1.9vh;border:2px solid var(--ink);border-radius:2vh;padding:.1vh 1vh;margin-left:.6vw;background:${
  { strong: "var(--yellow)", moderate: "#fff", mixed: "#fff", weak: "transparent" }[t]}">${t}</span>`;

window.DECK_DATA = {
  validation: `
    <div class="card"><div class="num">46.9%</div><p style="margin-top:1vh">of puppies already struggle when left alone</p></div>
    <div class="card"><div class="num">14 to 20%</div><p style="margin-top:1vh">of pet dogs have separation anxiety</p></div>
    <div class="card"><div class="num">$3.6B → $7B</div><p style="margin-top:1vh">India pet-care spend, FY24 to FY28</p></div>
    <div class="card"><div class="num">₹50k</div><p style="margin-top:1vh">a year spent by metro pet parents on pet care</p></div>
    <div class="card" style="grid-column:1/3;background:var(--yellow)"><h3>Pet cams don't fix it</h3>
      <p>They alert on barking and wait for the owner to watch. None detect anxiety.</p></div>`,
  validationSrc: `Sources: Dale et al. 2024, <i>Animal Welfare</i>, n=145 (<a href="https://pmc.ncbi.nlm.nih.gov/articles/PMC11655275/">link</a>) ·
    Pankratz et al. 2021 (<a href="https://pmc.ncbi.nlm.nih.gov/articles/PMC8720769/">link</a>) ·
    Redseer 2024, both India figures (<a href="https://redseer.com/wp-content/uploads/2024/10/Indias-Petcare-Market-Opportunities-in-an-Evolving-Market.pdf">link</a>) ·
    Furbo, Petcube product pages.`,

  anxietyMap: `
    <div class="card"><h3>1 · When it starts</h3><p>
      First minutes after he leaves<br>
      Routine changes (back to office)<br>
      Fuss on return: <b>6x</b> risk</p></div>
    <div class="card"><h3>2 · What we catch</h3><p>
      Anxiety and behaviour, read from signals:<br>
      🎤 <b>Mic:</b> barking, whining<br>
      📷 <b>Camera:</b> pacing, panting, chewing at the door</p></div>
    <div class="card"><h3>3 · What calms</h3><p style="line-height:2">
      🔊 Owner's voice ${badge("mixed")}<br>
      🦴 Treat, when calm ${badge("moderate")}<br>
      🎾 Favourite toy ${badge("weak")}<br>
      📹 Video ${badge("weak")}</p></div>
    <div class="card" style="grid-column:1/4;background:var(--yellow);padding:1.6vh 2.2vw">
      <p style="font-size:2.4vh;margin:0"><b>No single fix works for every dog.</b> So Ravi chooses, and Dogify learns what works for <i>Pablo</i>.</p></div>`,
  anxietySrc: `Sources: Palestrini 2010 via Sargisson 2014 (<a href="https://pmc.ncbi.nlm.nih.gov/articles/PMC7521022/">link</a>) · Harvey 2022 (<a href="https://pmc.ncbi.nlm.nih.gov/articles/PMC8868415/">link</a>) ·
    Dale 2024 (<a href="https://pmc.ncbi.nlm.nih.gov/articles/PMC11655275/">link</a>) · VCA, ASPCA ·
    Shin &amp; Shin 2016 (<a href="https://pubmed.ncbi.nlm.nih.gov/26645334/">link</a>) · Kinnaird &amp; Wells 2022 · Shnookal et al. 2024 · Chan et al. 2023 · full list in research.md`,
};
