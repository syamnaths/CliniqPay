import test from 'node:test';
import assert from 'node:assert/strict';
import { priorityPlan } from '../starter/docs/app-map/priority-plan.mjs';
const map=(id,extra={})=>({id,title:id,status:'planned',...extra});
test('continues active work before the next ordered map',()=>{
 const p=priorityPlan([map('a'),map('b',{status:'building'})],{buildOrder:['a','b']});assert.equal(p.next,'b');assert.equal(p.queue[0].priority,null);
});
test('skips blocked work, waits for prerequisites, and finishes honestly',()=>{
 const maps=[map('a',{blockedBy:'Need owner input'}),map('b',{dependsOn:['a']}),map('c')];
 assert.equal(priorityPlan(maps,{buildOrder:['a','b','c']}).next,'c');
 assert.equal(priorityPlan(maps.slice(0,2),{buildOrder:['a','b']}).next,null);
 maps.forEach(g=>g.status='delivered');assert.equal(priorityPlan(maps,{buildOrder:['a','b','c']}).queue.length,0);
});
test('rejects cycles, invalid priority and dependency order; rejects too much active work',()=>{
 assert.ok(priorityPlan([map('a',{dependsOn:['b']}),map('b',{dependsOn:['a']})],{buildOrder:['a','b']}).issues.length);
 assert.ok(priorityPlan([map('a',{priority:{urgent:true}})],{buildOrder:['a']}).issues.length);
 const p=priorityPlan([map('a',{status:'building'}),map('b',{status:'building'})],{buildOrder:['a','b']});assert.equal(p.next,null);assert.match(p.issues.join(' '),/Multiple building maps/);
});

test('release waits for every feature even when an earlier feature is blocked',()=>{
 const maps=[map('a',{group:'Features',blockedBy:'Owner input'}),map('release')];
 const p=priorityPlan(maps,{buildOrder:['a','release']});assert.equal(p.next,null);assert.deepEqual(p.queue[1].blockers,['Needs a']);
});

test('blocked active work requires an explicit checkpoint before switching',()=>{
 const maps=[map('a',{status:'building',blockedBy:'Waiting for access'}),map('b')];
 const p=priorityPlan(maps,{buildOrder:['a','b']});assert.equal(p.next,null);assert.equal(p.warnings.length,1);
 maps[0].status='planned';assert.equal(priorityPlan(maps,{buildOrder:['a','b']}).next,'b');
});
test('implicit release dependencies cannot hide a cycle or wrong release order',()=>{
 assert.ok(priorityPlan([map('a',{group:'Features',dependsOn:['release']}),map('release')],{buildOrder:['a','release']}).issues.some(x=>x.includes('cycle')));
 assert.ok(priorityPlan([map('a',{group:'Features'}),map('release')],{buildOrder:['release','a']}).issues.some(x=>x.includes('must come first')));
});
test('unfinished dependencies must be scheduled and delivered dependants remain honest',()=>{
 assert.ok(priorityPlan([map('a',{dependsOn:['system']}),map('system')],{buildOrder:['a']}).issues.some(x=>x.includes('missing from build order')));
 assert.ok(priorityPlan([map('a',{status:'delivered',dependsOn:['b']}),map('b')],{buildOrder:['b','a']}).issues.some(x=>x.includes('delivered before dependency')));
});
test('urgency never overrides a prerequisite or agreed order',()=>{
 const p=priorityPlan([map('a'),map('b',{dependsOn:['a'],priority:{rock:'big',important:true,urgent:true,reason:'Service outage'}})],{buildOrder:['a','b']});assert.equal(p.next,'a');
});
