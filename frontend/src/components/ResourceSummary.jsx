import { CheckCircle2, DollarSign, Server, HardDrive, Network, Globe, AlertCircle } from 'lucide-react'

function ResourceSummary({ summary, costEstimate, createdResource }) {
  if (!summary && !costEstimate && !createdResource) return null

  return (
    <div className="mb-4 space-y-3 animate-slide-up">
      {/* Created Resource Success Card */}
      {createdResource && createdResource.success && (
        <div className="glass rounded-2xl p-4 border border-green-500/30">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-xl bg-green-500/20 flex items-center justify-center">
              <CheckCircle2 className="w-5 h-5 text-green-400" />
            </div>
            <div>
              <h3 className="font-semibold text-green-400">Resource Created</h3>
              <p className="text-xs text-slate-400">{createdResource.resource_type}</p>
            </div>
          </div>
          
          <div className="space-y-2 text-sm">
            <div className="flex items-center justify-between">
              <span className="text-slate-400">Name</span>
              <span className="text-white font-medium">{createdResource.resource_name}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-400">Region</span>
              <span className="text-white">{createdResource.region}</span>
            </div>
            {createdResource.resource_id && (
              <div className="mt-3 pt-3 border-t border-white/10">
                <span className="text-slate-400 text-xs block mb-1">Resource ID</span>
                <code className="text-xs text-azure-300 bg-azure-500/10 px-2 py-1 rounded block break-all">
                  {createdResource.resource_id}
                </code>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Cost Estimate Card */}
      {costEstimate && !createdResource && (
        <div className="glass rounded-2xl p-4">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-xl bg-amber-500/20 flex items-center justify-center">
              <DollarSign className="w-5 h-5 text-amber-400" />
            </div>
            <div>
              <h3 className="font-semibold text-white">Estimated Cost</h3>
              <p className="text-2xl font-bold gradient-text">
                ${costEstimate.estimated_monthly_cost?.toFixed(2)}/mo
              </p>
            </div>
          </div>

          {costEstimate.breakdown && costEstimate.breakdown.length > 0 && (
            <div className="space-y-2 mt-4">
              <p className="text-xs text-slate-400 uppercase tracking-wider">Breakdown</p>
              {costEstimate.breakdown.map((item, index) => (
                <div key={index} className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    <ResourceIcon component={item.component} />
                    <span className="text-slate-300">{item.component}</span>
                  </div>
                  <span className="text-white font-medium">${item.monthly_cost?.toFixed(2)}</span>
                </div>
              ))}
            </div>
          )}

          {costEstimate.disclaimer && (
            <div className="flex items-start gap-2 mt-4 p-3 rounded-lg bg-amber-500/10 border border-amber-500/20">
              <AlertCircle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
              <p className="text-xs text-amber-200/80">{costEstimate.disclaimer}</p>
            </div>
          )}
        </div>
      )}

      {/* Resource Summary Card */}
      {summary && !createdResource && (
        <div className="glass rounded-2xl p-4">
          <h3 className="font-semibold text-white mb-3 flex items-center gap-2">
            <Server className="w-4 h-4 text-azure-400" />
            Configuration Summary
          </h3>
          
          <div className="grid grid-cols-2 gap-3 text-sm">
            {summary.resource_type && (
              <div>
                <span className="text-slate-400 text-xs block">Resource Type</span>
                <span className="text-white capitalize">{summary.resource_type}</span>
              </div>
            )}
            {summary.region && (
              <div>
                <span className="text-slate-400 text-xs block">Region</span>
                <span className="text-white">{summary.region}</span>
              </div>
            )}
            {summary.resource_group && (
              <div>
                <span className="text-slate-400 text-xs block">Resource Group</span>
                <span className="text-white">
                  {summary.resource_group}
                  {summary.create_new_rg && <span className="text-azure-400 text-xs ml-1">(new)</span>}
                </span>
              </div>
            )}
          </div>

          {summary.configuration && Object.keys(summary.configuration).length > 0 && (
            <div className="mt-4 pt-4 border-t border-white/10">
              <span className="text-xs text-slate-400 uppercase tracking-wider">Details</span>
              <div className="mt-2 space-y-1">
                {Object.entries(summary.configuration).map(([key, value]) => {
                  if (key.startsWith('_')) return null
                  const displayKey = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
                  const displayValue = typeof value === 'object' 
                    ? JSON.stringify(value) 
                    : String(value)
                  
                  return (
                    <div key={key} className="flex items-center justify-between text-sm">
                      <span className="text-slate-400">{displayKey}</span>
                      <span className="text-white truncate max-w-[60%] text-right" title={displayValue}>
                        {displayValue.length > 30 ? displayValue.substring(0, 30) + '...' : displayValue}
                      </span>
                    </div>
                  )
                })}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function ResourceIcon({ component }) {
  const comp = component?.toLowerCase() || ''
  
  if (comp.includes('vm') || comp.includes('compute') || comp.includes('node')) {
    return <Server className="w-4 h-4 text-azure-400" />
  }
  if (comp.includes('disk') || comp.includes('storage')) {
    return <HardDrive className="w-4 h-4 text-azure-400" />
  }
  if (comp.includes('network') || comp.includes('ip') || comp.includes('load')) {
    return <Network className="w-4 h-4 text-azure-400" />
  }
  if (comp.includes('aks') || comp.includes('management')) {
    return <Globe className="w-4 h-4 text-azure-400" />
  }
  
  return <div className="w-4 h-4 rounded-full bg-azure-500/30" />
}

export default ResourceSummary

