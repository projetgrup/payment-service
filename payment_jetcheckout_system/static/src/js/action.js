// /** @odoo-module **/

// import { patch } from "@web/core/utils/patch";
// import { rpcService } from "@web/core/network/rpc_service";

// // Convert action_id to action in URL hash on page load and hash changes
// function convertActionIdToAction() {
//     const hash = window.location.hash;
//     if (hash && hash.includes('action_id=')) {
//         const newHash = hash.replace(/action_id=(\d+)/, 'action=$1');
//         if (newHash !== hash) {
//             window.location.hash = newHash;
//         }
//     }
// }

// convertActionIdToAction();

// window.addEventListener('hashchange', convertActionIdToAction);

// patch(rpcService, "payment_jetcheckout_system.rpcService", {
//     start(env) {
//         const originalRpc = this._super(env);
        
//         return async function rpc(route, params = {}, settings) {
            
//             if (route === "/web/action/load" && env.services.user.context.system) {
                
//                 const router = env.services.router;
//                 const menu_id = router.current.hash.menu_id;
//                 const cids = router.current.hash.cids;
                
                
//                 const state = await originalRpc("/web/system/load", {
//                     action: params.action_id,
//                     menu_id: menu_id,
//                     cids: cids
//                 }, settings);
                
//                 console.log("[System RPC] System conversion result:", state);
                
//                 if (state.action) {
//                     console.log("[System RPC] Updating hash action from", router.current.hash.action, "to", state.action);
//                     router.current.hash.action = state.action;
//                 }
//                 if (state.menu_id) {
//                     console.log("[System RPC] Updating hash menu_id from", router.current.hash.menu_id, "to", state.menu_id);
//                     router.current.hash.menu_id = state.menu_id;
//                 }
                
//                 try {
//                     router.pushState(router.current.hash, { replace: true });
//                     console.log("[System RPC] Updated URL hash");
//                 } catch (e) {
//                     console.error("[System RPC] Error updating hash:", e);
//                 }
                
//                 const finalActionId = state.action || params.action_id;
                
//                 const result = await originalRpc("/web/action/load", {
//                     action_id: finalActionId,
//                     additional_context: params.additional_context
//                 }, settings);
                
//                 return result;
//             }
            
//             return originalRpc(route, params, settings);
//         };
//     }
// });